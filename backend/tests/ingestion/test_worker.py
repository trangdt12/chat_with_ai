import asyncio

from sqlalchemy import delete, func, select

from app.ingestion.embeddings import FakeEmbedder
from app.ingestion.worker import claim_next_document, process_document, recover_stuck_documents
from app.models import Chunk, Document
from tests.helpers import add_document
from tests.pdf_factory import CORRUPT_PDF, encrypt_pdf, make_pdf, sample_pdf


async def _uploaded(db, seeded, filename="a.pdf", data=None) -> Document:
    return await add_document(
        db, seeded.doc_set_id, seeded.users["lan@demo.local"], filename, status="uploaded", data=data
    )


async def _chunk_count(db, doc_id=None) -> int:
    q = select(func.count()).select_from(Chunk)
    if doc_id is not None:
        q = q.where(Chunk.document_id == doc_id)
    return await db.scalar(q)


async def _reload(db, doc_id) -> Document | None:
    db.expire_all()
    return await db.get(Document, doc_id)


async def test_worker_happy_path(db, seeded):
    doc = await _uploaded(db, seeded)
    assert await claim_next_document() == doc.id
    await process_document(doc.id, FakeEmbedder())

    doc = await _reload(db, doc.id)
    assert (doc.status, doc.progress, doc.pages, doc.error_code) == ("ready", 100, 2, None)
    chunks = (await db.scalars(select(Chunk).where(Chunk.document_id == doc.id).order_by(Chunk.chunk_index))).all()
    assert len(chunks) > 0
    assert {c.page_number for c in chunks} == {1, 2}
    assert all(c.doc_set_id == seeded.doc_set_id for c in chunks)
    assert "HD-2024-017" in chunks[0].content and "trang" not in chunks[0].content[:20]  # không lưu tiền tố


async def test_worker_rerun_idempotent(db, seeded):
    doc = await _uploaded(db, seeded)
    await process_document(doc.id, FakeEmbedder())
    first = await _chunk_count(db, doc.id)
    await process_document(doc.id, FakeEmbedder())
    assert await _chunk_count(db, doc.id) == first


async def test_worker_pdf_errors(db, seeded):
    cases = {
        "encrypted": encrypt_pdf(sample_pdf()),
        "corrupt": CORRUPT_PDF,
        "no_text": make_pdf(["", "", "", "", "trang duy nhat co chu that su dai hon ba muoi ky tu"]),
        "too_many_pages": make_pdf(["x"] * 201),
    }
    ids = {code: (await _uploaded(db, seeded, f"{code}.pdf", data)).id for code, data in cases.items()}
    for doc_id in ids.values():
        await process_document(doc_id, FakeEmbedder())
    for code, doc_id in ids.items():
        doc = await _reload(db, doc_id)
        assert (doc.status, doc.error_code) == ("failed", code)
    assert await _chunk_count(db) == 0


async def test_recover_stuck_processing(db, seeded):
    doc = await _uploaded(db, seeded)
    assert await claim_next_document() == doc.id  # giả lập worker chết khi đang processing
    assert await recover_stuck_documents() == 1
    assert (await _reload(db, doc.id)).status == "uploaded"
    assert await claim_next_document() == doc.id


async def test_claim_skip_locked(db, seeded):
    a = await _uploaded(db, seeded, "a.pdf")
    b = await _uploaded(db, seeded, "b.pdf")
    got = await asyncio.gather(claim_next_document(), claim_next_document())
    assert set(got) == {a.id, b.id}
    assert await claim_next_document() is None


async def test_worker_document_deleted_midway(db, seeded):
    long_pdf = make_pdf([f"Trang {i}. " + "Noi dung hop dong rat dai. " * 60 for i in range(1, 40)])
    doc = await _uploaded(db, seeded, data=long_pdf)
    loop = asyncio.get_running_loop()

    async def purge():
        await db.execute(delete(Document).where(Document.id == doc.id))
        await db.commit()

    class DeletingEmbedder(FakeEmbedder):
        calls = 0

        def embed_documents(self, texts):
            DeletingEmbedder.calls += 1
            if DeletingEmbedder.calls == 1:
                # chạy trong thread của asyncio.to_thread → nhờ event loop chính xóa tài liệu
                asyncio.run_coroutine_threadsafe(purge(), loop).result()
            return super().embed_documents(texts)

    await process_document(doc.id, DeletingEmbedder())  # không ném lỗi
    assert await _reload(db, doc.id) is None
    assert await _chunk_count(db) == 0
