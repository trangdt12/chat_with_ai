"""Worker xử lý tài liệu: lấy tài liệu `uploaded` → đọc PDF → chia đoạn → embedding → `ready`.

Chạy: `python -m app.ingestion.worker`. Log chỉ có document_id, số trang, số đoạn, thời gian — không có nội dung.
"""

import asyncio
import logging
import os
import time
import uuid

from sqlalchemy import delete, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal
from app.ingestion.chunker import ChunkDraft, chunk_pages
from app.ingestion.embeddings import EmbedderProtocol, embedding_text, get_embedder
from app.ingestion.pdf import PdfError, extract_pages, is_scanned
from app.models import Chunk, Document

log = logging.getLogger("app.worker")

EMBED_BATCH = 32

_CLAIM_SQL = text(
    """
    UPDATE documents SET status = 'processing', progress = 0, error_code = NULL
    WHERE id = (SELECT id FROM documents WHERE status = 'uploaded'
                ORDER BY uploaded_at FOR UPDATE SKIP LOCKED LIMIT 1)
    RETURNING id
    """
)


async def recover_stuck_documents() -> int:
    """Tài liệu kẹt ở `processing` (worker chết giữa chừng) được đưa về `uploaded` để xử lý lại."""
    async with SessionLocal() as db:
        result = await db.execute(
            update(Document).where(Document.status == "processing").values(status="uploaded", progress=0)
        )
        await db.commit()
        return result.rowcount or 0


async def claim_next_document() -> uuid.UUID | None:
    async with SessionLocal() as db:
        doc_id = await db.scalar(_CLAIM_SQL)
        await db.commit()
        return doc_id


async def _update_if_present(doc_id: uuid.UUID, **values) -> bool:
    """Cập nhật dòng documents; False nếu tài liệu đã bị gỡ (dòng hoặc file không còn)."""
    async with SessionLocal() as db:
        path = await db.scalar(
            update(Document).where(Document.id == doc_id).values(**values).returning(Document.file_path)
        )
        await db.commit()
    if path is None or not os.path.exists(path):
        log.info("document %s đã bị gỡ trong lúc xử lý — bỏ qua", doc_id)
        return False
    return True


async def _fail(doc_id: uuid.UUID, code: str) -> None:
    await _update_if_present(doc_id, status="failed", error_code=code, progress=0)
    log.info("document %s failed: %s", doc_id, code)


async def process_document(doc_id: uuid.UUID, embedder: EmbedderProtocol) -> None:
    settings = get_settings()
    started = time.monotonic()
    async with SessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if doc is None:
            return
        path, filename = doc.file_path, doc.filename

    # Bước 1–4: đọc PDF, kiểm tra mật khẩu / hỏng / số trang, trích xuất chữ.
    try:
        pages = await asyncio.to_thread(extract_pages, path, settings.upload_max_pages)
    except PdfError as e:
        await _fail(doc_id, e.code)
        return
    except OSError:
        await _fail(doc_id, "corrupt")  # file đã bị gỡ thì _fail chỉ log và bỏ qua
        return
    if not await _update_if_present(doc_id, pages=len(pages)):
        return

    # Bước 5–6: phát hiện bản scan, chia đoạn.
    drafts = chunk_pages(pages, settings.chunk_max_chars)
    if is_scanned(pages) or not drafts:
        await _fail(doc_id, "no_text")
        return
    if not await _update_if_present(doc_id, progress=10):
        return

    # Bước 7: embedding theo lô; mỗi lô commit progress riêng để FE thấy.
    vectors: list[list[float]] = []
    for start in range(0, len(drafts), EMBED_BATCH):
        batch = drafts[start : start + EMBED_BATCH]
        texts = [embedding_text(filename, d.page_number, d.content) for d in batch]
        try:
            vectors.extend(await asyncio.to_thread(embedder.embed_documents, texts))
        except Exception as e:
            log.warning("document %s: lỗi embedding %s", doc_id, type(e).__name__)
            await _fail(doc_id, "corrupt")
            return
        progress = 10 + 85 * len(vectors) // len(drafts)
        if not await _update_if_present(doc_id, progress=progress):
            return

    # Bước 8: xóa chunk cũ rồi ghi toàn bộ trong một transaction (chạy lại cho cùng kết quả).
    async with SessionLocal() as db:
        if not await _save_chunks(db, doc_id, drafts, vectors):
            return
    log.info(
        "document %s ready: %d trang, %d đoạn, %.1fs", doc_id, len(pages), len(drafts), time.monotonic() - started
    )


async def _save_chunks(
    db: AsyncSession, doc_id: uuid.UUID, drafts: list[ChunkDraft], vectors: list[list[float]]
) -> bool:
    # Khóa dòng documents: nếu admin đang gỡ (T-14) thì chờ; gỡ xong thì không còn dòng để ghi.
    doc = await db.get(Document, doc_id, with_for_update=True)
    if doc is None or not os.path.exists(doc.file_path):
        log.info("document %s đã bị gỡ trước khi lưu đoạn — bỏ qua", doc_id)
        await db.rollback()
        return False
    await db.execute(delete(Chunk).where(Chunk.document_id == doc_id))
    db.add_all(
        Chunk(
            document_id=doc_id,
            doc_set_id=doc.doc_set_id,
            page_number=d.page_number,
            chunk_index=d.chunk_index,
            content=d.content,
            embedding=v,
        )
        for d, v in zip(drafts, vectors, strict=True)
    )
    doc.status = "ready"
    doc.progress = 100
    doc.error_code = None
    await db.commit()
    return True


async def run_forever() -> None:
    settings = get_settings()
    embedder = await asyncio.to_thread(get_embedder)  # tải model 1 lần khi khởi động
    recovered = await recover_stuck_documents()
    log.info("worker started (đưa %d tài liệu kẹt về hàng đợi)", recovered)
    while True:
        doc_id = await claim_next_document()
        if doc_id is None:
            await asyncio.sleep(settings.worker_poll_seconds)
            continue
        try:
            await process_document(doc_id, embedder)
        except Exception:
            log.exception("document %s: lỗi không mong đợi", doc_id)
            await _fail(doc_id, "corrupt")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run_forever())
