import asyncio
import uuid
from pathlib import Path

from sqlalchemy import func, select

from app.config import get_settings
from app.models import AuditLog, Document
from tests.pdf_factory import DOCX_BYTES, sample_pdf


def _pdf(name: str = "a.pdf", data: bytes | None = None):
    return ("files", (name, data if data is not None else sample_pdf(), "application/pdf"))


async def _confirm(c, dsid) -> None:
    r = await c.post(f"/api/v1/doc-sets/{dsid}/classification-confirmations")
    assert r.status_code == 201, r.text


async def _count_docs(db) -> int:
    return await db.scalar(select(func.count()).select_from(Document))


async def test_requires_classification(db, login_as, seeded):
    lan = await login_as("lan@demo.local")
    url = f"/api/v1/doc-sets/{seeded.doc_set_id}/documents"
    r = await lan.post(url, files=[_pdf()])
    assert r.status_code == 409
    assert r.json()["code"] == "CLASSIFICATION_REQUIRED"

    await _confirm(lan, seeded.doc_set_id)
    assert (await lan.post(url, files=[_pdf()])).status_code == 200
    actions = set(await db.scalars(select(AuditLog.action)))
    assert {"classification_confirm", "upload"} <= actions


async def test_single_pdf_ok(db, login_as, seeded):
    lan = await login_as("lan@demo.local")
    await _confirm(lan, seeded.doc_set_id)
    r = await lan.post(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents", files=[_pdf("HopDong.pdf")])
    assert r.status_code == 200
    [res] = r.json()
    assert res["status"] == "uploaded" and res["filename"] == "HopDong.pdf" and res["error_code"] is None

    doc = await db.get(Document, uuid.UUID(res["id"]))
    assert doc.status == "uploaded" and doc.pages is None
    assert doc.uploaded_by == seeded.users["lan@demo.local"]
    assert Path(doc.file_path) == Path(get_settings().files_dir) / str(seeded.doc_set_id) / f"{doc.id}.pdf"
    assert Path(doc.file_path).read_bytes() == sample_pdf()

    audit = await db.scalar(select(AuditLog).where(AuditLog.action == "upload"))
    assert audit.document_id == doc.id
    assert audit.meta == {"size_bytes": doc.size_bytes}


async def test_not_pdf_magic_bytes(db, login_as, seeded):
    minh = await login_as("minh@demo.local")
    await _confirm(minh, seeded.doc_set_id)
    r = await minh.post(
        f"/api/v1/doc-sets/{seeded.doc_set_id}/documents",
        files=[_pdf("BaoCao.pdf", DOCX_BYTES), _pdf("ok.pdf")],
    )
    first, second = r.json()
    assert first == {"filename": "BaoCao.pdf", "id": None, "status": None, "error_code": "NOT_PDF"}
    assert second["status"] == "uploaded"
    assert await _count_docs(db) == 1


async def test_too_large(db, login_as, seeded, monkeypatch):
    monkeypatch.setattr(get_settings(), "upload_max_bytes", 1000)
    lan = await login_as("lan@demo.local")
    await _confirm(lan, seeded.doc_set_id)
    big = sample_pdf() + b"0" * 5000
    r = await lan.post(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents", files=[_pdf("big.pdf", big)])
    assert r.json()[0]["error_code"] == "FILE_TOO_LARGE"
    assert await _count_docs(db) == 0
    folder = Path(get_settings().files_dir) / str(seeded.doc_set_id)
    assert list(folder.glob("*.tmp")) == []


async def test_batch_one_too_large_others_ok(db, login_as, seeded, monkeypatch):
    monkeypatch.setattr(get_settings(), "upload_max_bytes", 5000)
    minh = await login_as("minh@demo.local")
    await _confirm(minh, seeded.doc_set_id)
    files = [_pdf(f"f{i}.pdf") for i in range(4)] + [_pdf("big.pdf", sample_pdf() + b"0" * 10_000)]
    r = await minh.post(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents", files=files)
    codes = [x["error_code"] for x in r.json()]
    assert codes == [None, None, None, None, "FILE_TOO_LARGE"]
    assert await _count_docs(db) == 4


async def test_member_cannot_batch(db, login_as, seeded):
    lan = await login_as("lan@demo.local")
    await _confirm(lan, seeded.doc_set_id)
    r = await lan.post(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents", files=[_pdf("a.pdf"), _pdf("b.pdf")])
    assert r.status_code == 403
    assert "Vui lòng tải từng file" in r.json()["message"]
    assert await _count_docs(db) == 0


async def test_duplicate_name_renamed(login_as, seeded):
    lan = await login_as("lan@demo.local")
    await _confirm(lan, seeded.doc_set_id)
    url = f"/api/v1/doc-sets/{seeded.doc_set_id}/documents"
    assert (await lan.post(url, files=[_pdf("a.pdf")])).json()[0]["filename"] == "a.pdf"
    assert (await lan.post(url, files=[_pdf("a.pdf")])).json()[0]["filename"] == "a (2).pdf"
    assert (await lan.post(url, files=[_pdf("a.pdf")])).json()[0]["filename"] == "a (3).pdf"


async def test_concurrent_last_slot(db, login_as, seeded, monkeypatch):
    monkeypatch.setattr(get_settings(), "doc_set_max_documents", 3)
    lan = await login_as("lan@demo.local")
    minh = await login_as("minh@demo.local")
    url = f"/api/v1/doc-sets/{seeded.doc_set_id}/documents"
    for c in (lan, minh):
        await _confirm(c, seeded.doc_set_id)
    await minh.post(url, files=[_pdf("x1.pdf"), _pdf("x2.pdf")])

    r1, r2 = await asyncio.gather(lan.post(url, files=[_pdf("l.pdf")]), minh.post(url, files=[_pdf("m.pdf")]))
    codes = sorted(str(r.json()[0]["error_code"]) for r in (r1, r2))
    assert codes == ["DOC_SET_FULL", "None"]
    assert await _count_docs(db) == 3


async def test_admin_not_member_forbidden(login_as, seeded):
    hung = await login_as("hung@demo.local")
    r = await hung.post(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents", files=[_pdf()])
    assert r.status_code == 403
    r = await hung.post(f"/api/v1/doc-sets/{seeded.doc_set_id}/classification-confirmations")
    assert r.status_code == 403

