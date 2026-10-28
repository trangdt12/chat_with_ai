import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select

from app.models import AuditLog, Chunk, Citation, Document
from tests.helpers import add_chunks, add_document
from tests.sse_helpers import Env


async def test_admin_lists_metadata_only(db, login_as, seeded):
    await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "HopDongKhung.pdf")
    await add_document(db, seeded.doc_set_id, seeded.users["minh@demo.local"], "BaoGia_100%.pdf")
    hung = await login_as("hung@demo.local")
    r = await hung.get(f"/api/v1/admin/doc-sets/{seeded.doc_set_id}/documents")
    assert r.status_code == 200
    assert {d["filename"] for d in r.json()} == {"HopDongKhung.pdf", "BaoGia_100%.pdf"}
    assert set(r.json()[0]) == {
        "id", "filename", "pages", "size_bytes", "status", "error_code", "uploaded_by_email", "uploaded_at",
    }
    r = await hung.get(f"/api/v1/admin/doc-sets/{seeded.doc_set_id}/documents", params={"q": "100%"})
    assert [d["filename"] for d in r.json()] == ["BaoGia_100%.pdf"]


async def test_admin_cannot_open_content(db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"])
    hung = await login_as("hung@demo.local")
    assert (await hung.get(f"/api/v1/documents/{doc.id}/file")).status_code == 403


async def test_purge_removes_chunks_file_and_redacts_citations(app, db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "HopDongKhung.pdf")
    doc_id, file_path = doc.id, doc.file_path  # db.expire_all() bên dưới làm hết hạn object
    await add_chunks(db, doc, ["Thời hạn thanh toán là 30 ngày kể từ ngày nhận hóa đơn."])
    env = Env(app, db, seeded, await login_as("lan@demo.local"))
    try:
        events = await env.ask_events(await env.conversation(), "Thời hạn thanh toán là bao lâu?")
        assert events[-1][1]["answer_type"] == "answered"
        citation_id = events[-1][1]["citations"][0]["citation_id"]

        hung = await login_as("hung@demo.local")
        r = await hung.request(
            "DELETE", f"/api/v1/admin/documents/{doc.id}", json={"requested_by": "Trần Văn Minh", "reason": "Nhầm"}
        )
        assert r.status_code == 200 and r.json() == {"id": str(doc.id), "removed": True}

        assert not Path(file_path).exists()
        assert await db.scalar(select(func.count()).select_from(Chunk)) == 0
        db.expire_all()
        cit = await db.get(Citation, citation_id)
        assert (cit.removed, cit.snippet, cit.filename, cit.chunk_id) == (True, None, None, None)
        audit = await db.scalar(select(AuditLog).where(AuditLog.action == "remove_document"))
        assert audit.document_id == doc_id and audit.meta["reason"] == "Nhầm"

        # Lan: tài liệu biến khỏi danh sách; trích dẫn cũ → 410; hỏi lại → not_found.
        r = await env.lan.get(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents")
        assert r.json() == []
        assert (await env.lan.get(f"/api/v1/citations/{citation_id}")).status_code == 410
    finally:
        app.dependency_overrides.clear()


async def test_purge_then_query_not_found(app, db, login_as, seeded):
    keep = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "Khac.pdf")
    await add_chunks(db, keep, ["Điều khoản bảo mật thông tin khách hàng."])
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "HopDongKhung.pdf")
    await add_chunks(db, doc, ["Thời hạn thanh toán là 30 ngày kể từ ngày nhận hóa đơn."])
    hung = await login_as("hung@demo.local")
    await hung.request("DELETE", f"/api/v1/admin/documents/{doc.id}", json={"requested_by": "Minh", "reason": "Cũ"})

    env = Env(app, db, seeded, await login_as("lan@demo.local"))
    try:
        cid = await env.conversation()
        for q in ("Thời hạn thanh toán là bao lâu?", "thanh toán hóa đơn trong bao nhiêu ngày?"):
            events = await env.ask_events(cid, q)
            assert events[-1][1]["answer_type"] == "not_found"
    finally:
        app.dependency_overrides.clear()


async def test_purge_forbidden_for_non_admin(db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"])
    lan = await login_as("lan@demo.local")
    r = await lan.request("DELETE", f"/api/v1/admin/documents/{doc.id}", json={"requested_by": "x", "reason": "y"})
    assert r.status_code == 403
    assert await db.get(Document, doc.id) is not None


async def test_purge_validation(db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"])
    hung = await login_as("hung@demo.local")
    for body in ({"requested_by": "", "reason": "y"}, {"requested_by": "x", "reason": "   "}, {}):
        r = await hung.request("DELETE", f"/api/v1/admin/documents/{doc.id}", json=body)
        assert r.status_code == 422


async def test_purge_file_missing_on_disk_still_ok(db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"])
    Path(doc.file_path).unlink()
    hung = await login_as("hung@demo.local")
    r = await hung.request("DELETE", f"/api/v1/admin/documents/{doc.id}", json={"requested_by": "x", "reason": "y"})
    assert r.status_code == 200
    assert await db.scalar(select(AuditLog.id).where(AuditLog.action == "remove_document"))


async def _audit_page(client, seeded, **params):
    r = await client.get("/api/v1/admin/audit-logs", params={"doc_set_id": str(seeded.doc_set_id), **params})
    assert r.status_code == 200, r.text
    return r.json()


async def test_audit_query_filters_and_cursor(db, login_as, seeded):
    lan_id = seeded.users["lan@demo.local"]
    now = datetime.now(UTC)
    for i in range(5):
        ts = now - timedelta(minutes=i)
        db.add(AuditLog(user_id=lan_id, action="view_file", doc_set_id=seeded.doc_set_id, ts=ts))
    db.add(AuditLog(user_id=seeded.users["minh@demo.local"], action="upload", doc_set_id=seeded.doc_set_id, ts=now))
    db.add(AuditLog(user_id=lan_id, action="view_file", doc_set_id=seeded.doc_set_id, ts=now - timedelta(days=30)))
    await db.commit()
    hung = await login_as("hung@demo.local")  # login của admin không thuộc nhóm → không hiện

    page = await _audit_page(hung, seeded)
    assert [i["action"] for i in page["items"]].count("view_file") == 5  # bản ghi 30 ngày trước bị lọc
    assert all(i["action"] != "login" for i in page["items"])

    lan_items = (await _audit_page(hung, seeded, user_id=str(lan_id), action="view_file"))["items"]
    assert len(lan_items) == 5 and all(i["user_email"] == "lan@demo.local" for i in lan_items)

    p1 = await _audit_page(hung, seeded, action="view_file", limit=3)
    p2 = await _audit_page(hung, seeded, action="view_file", limit=3, cursor=p1["next_cursor"])
    assert len(p1["items"]) == 3 and len(p2["items"]) == 2 and p2["next_cursor"] is None
    assert not {i["id"] for i in p1["items"]} & {i["id"] for i in p2["items"]}
    ts = [i["ts"] for i in p1["items"] + p2["items"]]
    assert ts == sorted(ts, reverse=True)

    old_day = (now - timedelta(days=30)).astimezone(timezone(timedelta(hours=7))).date().isoformat()
    old = await _audit_page(hung, seeded, **{"from": old_day, "to": old_day, "action": "view_file"})
    assert len(old["items"]) == 1


async def test_audit_includes_member_logins_and_known_flow(app, db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "HopDongKhung.pdf")
    await add_chunks(db, doc, ["Thời hạn thanh toán là 30 ngày."])
    env = Env(app, db, seeded, await login_as("lan@demo.local"))
    try:
        await env.lan.post(f"/api/v1/doc-sets/{seeded.doc_set_id}/classification-confirmations")
        events = await env.ask_events(await env.conversation(), "Thời hạn thanh toán?")
        await env.lan.get(f"/api/v1/citations/{events[-1][1]['citations'][0]['citation_id']}")
    finally:
        app.dependency_overrides.clear()
    hung = await login_as("hung@demo.local")
    items = (await _audit_page(hung, seeded))["items"]
    actions = [i["action"] for i in reversed(items)]  # cũ → mới
    assert actions == ["login", "classification_confirm", "query", "view_citation"]
    assert items[-1]["user_email"] == "lan@demo.local"


async def test_audit_meta_never_contains_content(app, db, login_as, seeded):
    question = "Thời hạn thanh toán của hợp đồng khung?"
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "HopDongKhung.pdf")
    await add_chunks(db, doc, ["Thời hạn thanh toán của hợp đồng khung là 30 ngày."])
    env = Env(app, db, seeded, await login_as("lan@demo.local"))
    try:
        events = await env.ask_events(await env.conversation(), question)
        answer = "".join(d["text"] for n, d in events if n == "answer.delta")
        await env.lan.get(f"/api/v1/citations/{events[-1][1]['citations'][0]['citation_id']}")
    finally:
        app.dependency_overrides.clear()
    metas = (await db.scalars(select(AuditLog.meta).where(AuditLog.meta.is_not(None)))).all()
    dumped = json.dumps(metas, ensure_ascii=False)
    assert question not in dumped and answer not in dumped and "30 ngày" not in dumped


async def test_audit_document_filename_null_after_purge(db, login_as, seeded):
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "HopDongKhung.pdf")
    lan = await login_as("lan@demo.local")
    await lan.get(f"/api/v1/documents/{doc.id}/file")
    hung = await login_as("hung@demo.local")
    item = (await _audit_page(hung, seeded, action="view_file"))["items"][0]
    assert item["document_filename"] == "HopDongKhung.pdf"
    await hung.request("DELETE", f"/api/v1/admin/documents/{doc.id}", json={"requested_by": "x", "reason": "y"})
    item = (await _audit_page(hung, seeded, action="view_file"))["items"][0]
    assert item["document_filename"] is None and item["document_id"] == str(doc.id)
