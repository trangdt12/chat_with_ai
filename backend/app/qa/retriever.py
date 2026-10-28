"""ALG-03: tìm kiếm kết hợp vector (hiểu nghĩa, hỏi chéo Việt/Anh) + từ khóa (mã số, tên riêng), hợp nhất bằng RRF."""

import asyncio
import uuid
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.ingestion.embeddings import EmbedderProtocol
from app.models import Chunk, Document

RRF_K = 60
HNSW_EF_SEARCH = 80


@dataclass(frozen=True)
class Candidate:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int
    content: str


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int
    content: str
    score: float  # điểm RRF


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]  # ≤ retrieval_top_k, thứ tự = search_result_index gửi cho Claude
    max_cos: float  # cosine cao nhất của nhánh vector (0 nếu rỗng)
    fts_hits: int  # số kết quả nhánh từ khóa
    not_found: bool  # max_cos < τ và fts_hits == 0


def rrf_merge(
    branches: list[list[Candidate]], top_k: int, max_per_doc: int, k: int = RRF_K
) -> list[RetrievedChunk]:
    """rrf[id] = Σ_nhánh 1 / (k + rank) (rank từ 1); hòa điểm xếp theo chunk_id; tối đa max_per_doc đoạn/tài liệu."""
    scores: dict[uuid.UUID, float] = {}
    by_id: dict[uuid.UUID, Candidate] = {}
    for branch in branches:
        for rank, cand in enumerate(branch, start=1):
            scores[cand.chunk_id] = scores.get(cand.chunk_id, 0.0) + 1.0 / (k + rank)
            by_id.setdefault(cand.chunk_id, cand)

    ranked = sorted(scores, key=lambda cid: (-scores[cid], str(cid)))
    picked: list[RetrievedChunk] = []
    per_doc: dict[uuid.UUID, int] = {}
    for cid in ranked:
        c = by_id[cid]
        if per_doc.get(c.document_id, 0) >= max_per_doc:
            continue
        per_doc[c.document_id] = per_doc.get(c.document_id, 0) + 1
        picked.append(RetrievedChunk(c.chunk_id, c.document_id, c.filename, c.page, c.content, scores[cid]))
        if len(picked) == top_k:
            break
    return picked


def is_not_found(max_cos: float, fts_hits: int, tau: float) -> bool:
    return max_cos < tau and fts_hits == 0


_FTS_SQL = text(
    """
    SELECT c.id, c.document_id, d.filename, c.page_number, c.content, ts_rank_cd(c.tsv, q) AS r
    FROM chunks c JOIN documents d ON d.id = c.document_id,
         websearch_to_tsquery('simple', f_unaccent(:q)) q
    WHERE c.doc_set_id = :ds AND d.status = 'ready' AND c.tsv @@ q
    ORDER BY r DESC, c.id
    LIMIT :k
    """
)


async def _vector_branch(
    db: AsyncSession, doc_set_id: uuid.UUID, qvec: list[float], k: int
) -> tuple[list[Candidate], float]:
    await db.execute(text(f"SET LOCAL hnsw.ef_search = {HNSW_EF_SEARCH}"))
    distance = Chunk.embedding.cosine_distance(qvec)
    rows = await db.execute(
        select(
            Chunk.id,
            Chunk.document_id,
            Document.filename,
            Chunk.page_number,
            Chunk.content,
            (1 - distance).label("cos"),
        )
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.doc_set_id == doc_set_id, Document.status == "ready")
        .order_by(distance)
        .limit(k)
    )
    cands, max_cos = [], 0.0
    for cid, did, fname, page, content, cos in rows.all():
        cands.append(Candidate(cid, did, fname, page, content))
        max_cos = max(max_cos, float(cos))
    return cands, max_cos


async def _fts_branch(db: AsyncSession, doc_set_id: uuid.UUID, query: str, k: int) -> list[Candidate]:
    rows = await db.execute(_FTS_SQL, {"q": query, "ds": doc_set_id, "k": k})
    return [Candidate(cid, did, fname, page, content) for cid, did, fname, page, content, _ in rows.all()]


async def retrieve(
    db: AsyncSession, embedder: EmbedderProtocol, doc_set_id: uuid.UUID, query: str
) -> RetrievalResult:
    s = get_settings()
    qvec = await asyncio.to_thread(embedder.embed_query, query)
    vec_hits, max_cos = await _vector_branch(db, doc_set_id, qvec, s.retrieval_top_k_branch)
    fts_hits = await _fts_branch(db, doc_set_id, query, s.retrieval_top_k_branch)
    await db.commit()  # kết thúc transaction đọc (SET LOCAL hết hiệu lực)
    chunks = rrf_merge([vec_hits, fts_hits], s.retrieval_top_k, s.retrieval_max_per_doc)
    return RetrievalResult(
        chunks=chunks,
        max_cos=max_cos,
        fts_hits=len(fts_hits),
        not_found=is_not_found(max_cos, len(fts_hits), s.retrieval_not_found_tau),
    )
