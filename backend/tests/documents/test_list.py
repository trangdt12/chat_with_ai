from sqlalchemy import delete, func, select

from app.models import AuditLog, Document
from tests.helpers import add_document
from tests.pdf_factory import sample_pdf


async def test_list_documents_sorted_desc(db, login_as, seeded):
    lan_id = seeded.users["lan@demo.local"]
    for i in range(5):
        await add_document(db, seeded.doc_set_id, lan_id, f"f{i}.pdf", minutes_ago=10 - i)
    lan = await login_as("lan@demo.local")
    r = await lan.get(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents")
    assert r.status_code == 200
    body = r.json()
    assert [d["filename"] for d in body] == ["f4.pdf", "f3.pdf", "f2.pdf", "f1.pdf", "f0.pdf"]
    assert set(body[0]) == {
        "id", "filename", "pages", "size_bytes", "status", "progress", "error_code", "uploaded_by", "uploaded_at",
    }
    assert body[0]["uploaded_by"] == "Nguyễn Thị Lan"


async def test_list_documents_forbidden_for_outsider_and_admin(db, login_as, seeded):
    await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "BiMat.pdf")
    for email in ("tuan@demo.local", "hung@demo.local"):
        c = await login_as(email)
        r = await c.get(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents")
        assert r.status_code == 403
        assert "BiMat" not in r.text


async def test_view_list_audited_at_most_once_per_minute(db, login_as, seeded):
    lan = await login_as("lan@demo.local")
    for _ in range(3):
        assert (await lan.get(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents")).status_code == 200
    n = await db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == "view_list"))
    assert n == 1


async def test_open_file_ok_and_removed(db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"])
    lan = await login_as("lan@demo.local")
    r = await lan.get(f"/api/v1/documents/{doc.id}/file?page=2")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.headers["content-disposition"].startswith("inline")
    assert r.content == sample_pdf()

    await db.execute(delete(Document).where(Document.id == doc.id))
    await db.commit()
    r = await lan.get(f"/api/v1/documents/{doc.id}/file")
    assert r.status_code == 410
    assert r.json()["code"] == "DOCUMENT_REMOVED"


async def test_open_file_forbidden_for_outsider(db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "BiMat.pdf")
    for email in ("tuan@demo.local", "hung@demo.local"):
        c = await login_as(email)
        r = await c.get(f"/api/v1/documents/{doc.id}/file")
        assert r.status_code == 403
        assert "BiMat" not in r.text


async def test_open_file_writes_audit(db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"])
    lan = await login_as("lan@demo.local")
    await lan.get(f"/api/v1/documents/{doc.id}/file")
    audit = await db.scalar(select(AuditLog).where(AuditLog.action == "view_file"))
    assert audit.document_id == doc.id
    assert audit.user_id == seeded.users["lan@demo.local"]
