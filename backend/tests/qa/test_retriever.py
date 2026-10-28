import uuid

from app.ingestion.embeddings import FakeEmbedder
from app.models import DocSet
from app.qa.retriever import Candidate, is_not_found, retrieve, rrf_merge
from tests.helpers import add_chunks, add_document


def _cand(doc: uuid.UUID, n: int | None = None) -> Candidate:
    cid = uuid.UUID(int=n) if n is not None else uuid.uuid4()
    return Candidate(cid, doc, "f.pdf", 1, "x")


# ---------- hàm thuần ----------


def test_rrf_merge_order():
    d = uuid.uuid4()
    a, b, c = _cand(d, 1), _cand(d, 2), _cand(d, 3)
    merged = rrf_merge([[a, b], [a, c]], top_k=10, max_per_doc=10)
    assert [m.chunk_id for m in merged][0] == a.chunk_id
    assert merged[0].score == 1 / 61 + 1 / 61
    assert {m.chunk_id: m.score for m in merged}[b.chunk_id] == 1 / 62


def test_rrf_max_per_doc():
    big = uuid.uuid4()
    branch = [_cand(big) for _ in range(12)] + [_cand(uuid.uuid4()) for _ in range(3)]
    merged = rrf_merge([branch], top_k=10, max_per_doc=4)
    assert len(merged) == 7
    assert sum(1 for m in merged if m.document_id == big) == 4


def test_rrf_tie_deterministic():
    d = uuid.uuid4()
    x, y = _cand(d, 5), _cand(d, 9)
    first = rrf_merge([[x], [y]], top_k=10, max_per_doc=4)
    second = rrf_merge([[y], [x]], top_k=10, max_per_doc=4)
    assert [m.chunk_id for m in first] == [m.chunk_id for m in second] == [x.chunk_id, y.chunk_id]


def test_not_found_flag():
    assert is_not_found(0.2, 0, 0.35) is True
    assert is_not_found(0.2, 1, 0.35) is False
    assert is_not_found(0.5, 0, 0.35) is False


# ---------- tích hợp (Postgres thật + FakeEmbedder) ----------


async def _ready_doc(db, seeded, filename, contents, status="ready", doc_set_id=None):
    doc = await add_document(
        db, doc_set_id or seeded.doc_set_id, seeded.users["lan@demo.local"], filename, status=status
    )
    await add_chunks(db, doc, contents)
    return doc


async def test_retrieve_excludes_non_ready(db, seeded):
    ready = await _ready_doc(db, seeded, "ready.pdf", ["Thời hạn thanh toán là 30 ngày."])
    await _ready_doc(db, seeded, "proc.pdf", ["Thời hạn thanh toán là 45 ngày."], status="processing")
    await _ready_doc(db, seeded, "fail.pdf", ["Thời hạn thanh toán là 60 ngày."], status="failed")
    result = await retrieve(db, FakeEmbedder(), seeded.doc_set_id, "thời hạn thanh toán")
    assert result.chunks
    assert {c.document_id for c in result.chunks} == {ready.id}


async def test_retrieve_scoped_to_doc_set(db, seeded):
    other = DocSet(name="Bộ khác")
    db.add(other)
    await db.commit()
    await _ready_doc(db, seeded, "khac.pdf", ["Thời hạn thanh toán là 90 ngày."], doc_set_id=other.id)
    mine = await _ready_doc(db, seeded, "mine.pdf", ["Thời hạn thanh toán là 30 ngày."])
    result = await retrieve(db, FakeEmbedder(), seeded.doc_set_id, "thời hạn thanh toán")
    assert {c.document_id for c in result.chunks} == {mine.id}


async def test_fts_unaccent(db, seeded):
    doc = await _ready_doc(db, seeded, "hd.pdf", ["Hợp đồng khung số HD-2024-017 ký ngày 1/3."])
    result = await retrieve(db, FakeEmbedder(), seeded.doc_set_id, "hop dong khung")
    assert result.fts_hits == 1
    assert result.chunks[0].document_id == doc.id
    assert result.not_found is False


async def test_keyword_code_found(db, seeded):
    await _ready_doc(db, seeded, "a.pdf", [f"Điều khoản chung số {i} về bảo mật." for i in range(20)])
    target = await _ready_doc(db, seeded, "b.pdf", ["Phụ lục của hợp đồng HD-2024-017."])
    result = await retrieve(db, FakeEmbedder(), seeded.doc_set_id, "HD-2024-017")
    assert target.id in {c.document_id for c in result.chunks}


async def test_unrelated_question_not_found(db, seeded):
    await _ready_doc(db, seeded, "hd.pdf", ["Thời hạn thanh toán là 30 ngày kể từ ngày nhận hóa đơn."])
    result = await retrieve(db, FakeEmbedder(), seeded.doc_set_id, "Thủ đô của Pháp là gì?")
    assert result.fts_hits == 0
    assert result.not_found is True


async def test_max_per_doc_in_retrieve(db, seeded):
    await _ready_doc(db, seeded, "big.pdf", [f"Thời hạn thanh toán mục {i}." for i in range(10)])
    result = await retrieve(db, FakeEmbedder(), seeded.doc_set_id, "thời hạn thanh toán")
    assert len(result.chunks) == 4
