import uuid

from sqlalchemy import func, select

from app.models import AuditLog, Membership
from tests.pdf_factory import sample_pdf


def members_url(seeded, uid=None) -> str:
    base = f"/api/v1/admin/doc-sets/{seeded.doc_set_id}/members"
    return f"{base}/{uid}" if uid else base


async def test_admin_routes_forbidden_for_member_and_manager(login_as, seeded):
    lan_id = seeded.users["lan@demo.local"]
    routes = [
        ("GET", "/api/v1/admin/doc-sets", None),
        ("GET", members_url(seeded), None),
        ("POST", members_url(seeded), {"email": "tuan@demo.local", "role": "member"}),
        ("PATCH", members_url(seeded, lan_id), {"role": "manager"}),
        ("DELETE", members_url(seeded, lan_id), None),
        ("GET", f"/api/v1/admin/doc-sets/{seeded.doc_set_id}/documents", None),
        ("DELETE", f"/api/v1/admin/documents/{uuid.uuid4()}", {"requested_by": "x", "reason": "y"}),
        ("GET", f"/api/v1/admin/audit-logs?doc_set_id={seeded.doc_set_id}", None),
    ]
    for email in ("lan@demo.local", "minh@demo.local"):
        c = await login_as(email)
        for method, url, body in routes:
            r = await c.request(method, url, json=body)
            assert r.status_code == 403, (email, method, url)


async def test_list_doc_sets_and_members(login_as, seeded):
    hung = await login_as("hung@demo.local")
    r = await hung.get("/api/v1/admin/doc-sets")
    assert r.json() == [{"id": str(seeded.doc_set_id), "name": "Dự án X", "member_count": 3}]
    r = await hung.get(members_url(seeded))
    assert {m["email"]: m["role"] for m in r.json()} == {
        "lan@demo.local": "member",
        "minh@demo.local": "manager",
        "anh@demo.local": "member",
    }
    assert all(m["granted_at"] for m in r.json())


async def test_add_member_then_can_use_content(db, login_as, seeded):
    hung = await login_as("hung@demo.local")
    r = await hung.post(members_url(seeded), json={"email": "  Tuan@Demo.Local ", "role": "member"})
    assert r.status_code == 201
    assert r.json()["email"] == "tuan@demo.local" and r.json()["role"] == "member"

    tuan = await login_as("tuan@demo.local")
    assert (await tuan.get(f"/api/v1/doc-sets/{seeded.doc_set_id}/documents")).status_code == 200
    audit = await db.scalar(select(AuditLog).where(AuditLog.action == "member_add"))
    assert audit.meta == {"target_user_id": str(seeded.users["tuan@demo.local"]), "role": "member"}


async def test_add_member_unknown_email(db, login_as, seeded):
    hung = await login_as("hung@demo.local")
    before = await db.scalar(select(func.count()).select_from(Membership))
    r = await hung.post(members_url(seeded), json={"email": "nobody@demo.local", "role": "member"})
    assert r.status_code == 404 and r.json()["code"] == "USER_NOT_FOUND"
    assert await db.scalar(select(func.count()).select_from(Membership)) == before


async def test_add_member_duplicate(login_as, seeded):
    hung = await login_as("hung@demo.local")
    r = await hung.post(members_url(seeded), json={"email": "lan@demo.local", "role": "member"})
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_MEMBER"


async def test_remove_member_effective_next_request(db, login_as, seeded):
    anh = await login_as("anh@demo.local")
    url = f"/api/v1/doc-sets/{seeded.doc_set_id}/documents"
    assert (await anh.get(url)).status_code == 200

    hung = await login_as("hung@demo.local")
    r = await hung.delete(members_url(seeded, seeded.users["anh@demo.local"]))
    assert r.status_code == 204
    assert (await anh.get(url)).status_code == 403
    assert await db.scalar(select(AuditLog.id).where(AuditLog.action == "member_remove"))

    r = await hung.delete(members_url(seeded, seeded.users["anh@demo.local"]))
    assert r.status_code == 404


async def test_role_change_enables_batch_upload(db, login_as, seeded):
    lan = await login_as("lan@demo.local")
    await lan.post(f"/api/v1/doc-sets/{seeded.doc_set_id}/classification-confirmations")
    url = f"/api/v1/doc-sets/{seeded.doc_set_id}/documents"
    files = [("files", (name, sample_pdf(), "application/pdf")) for name in ("a.pdf", "b.pdf")]
    assert (await lan.post(url, files=files)).status_code == 403

    hung = await login_as("hung@demo.local")
    r = await hung.patch(members_url(seeded, seeded.users["lan@demo.local"]), json={"role": "manager"})
    assert r.status_code == 200 and r.json()["role"] == "manager"
    r = await lan.post(url, files=files)
    assert r.status_code == 200
    assert [x["status"] for x in r.json()] == ["uploaded", "uploaded"]

    audit = await db.scalar(select(AuditLog).where(AuditLog.action == "role_change"))
    assert audit.meta == {"target_user_id": str(seeded.users["lan@demo.local"]), "from": "member", "to": "manager"}


async def test_audit_meta_has_no_email(db, login_as, seeded):
    hung = await login_as("hung@demo.local")
    await hung.post(members_url(seeded), json={"email": "tuan@demo.local", "role": "member"})
    await hung.patch(members_url(seeded, seeded.users["tuan@demo.local"]), json={"role": "manager"})
    await hung.delete(members_url(seeded, seeded.users["tuan@demo.local"]))
    metas = (
        await db.scalars(
            select(AuditLog.meta).where(AuditLog.action.in_(("member_add", "role_change", "member_remove")))
        )
    ).all()
    assert len(metas) == 3
    for meta in metas:
        assert "@" not in str(meta)
        assert set(meta) <= {"target_user_id", "role", "from", "to"}
