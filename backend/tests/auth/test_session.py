from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update

from app.models import AuditLog, Session


async def test_unauthenticated_401(client, seeded):
    r = await client.get("/api/v1/me")
    assert r.status_code == 401
    assert r.json()["code"] == "UNAUTHENTICATED"


async def test_dev_users_lists_all(client, seeded):
    r = await client.get("/api/v1/auth/dev-users")
    assert r.status_code == 200
    assert {u["email"] for u in r.json()} == set(seeded.users)


async def test_login_unknown_email_404(client, seeded):
    r = await client.post("/api/v1/auth/login", json={"email": "nobody@demo.local"})
    assert r.status_code == 404
    assert r.json()["code"] == "USER_NOT_FOUND"


async def test_login_sets_cookie_and_me(login_as, seeded):
    lan = await login_as("lan@demo.local")
    r = await lan.get("/api/v1/me")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "lan@demo.local"
    assert body["is_admin"] is False
    assert body["doc_sets"] == [{"id": str(seeded.doc_set_id), "name": "Dự án X", "role": "member"}]


async def test_token_not_stored_in_plaintext(db, login_as):
    lan = await login_as("lan@demo.local")
    token = lan.cookies["cwd_session"]
    assert await db.get(Session, token) is None
    assert await db.scalar(select(func.count()).select_from(Session)) == 1


async def test_idle_expired_401(db, login_as):
    lan = await login_as("lan@demo.local")
    await db.execute(update(Session).values(last_seen_at=datetime.now(UTC) - timedelta(hours=9)))
    await db.commit()
    assert (await lan.get("/api/v1/me")).status_code == 401


async def test_logout_invalidates(login_as):
    lan = await login_as("lan@demo.local")
    token = lan.cookies["cwd_session"]
    assert (await lan.post("/api/v1/auth/logout")).status_code == 204
    lan.cookies.set("cwd_session", token)
    assert (await lan.get("/api/v1/me")).status_code == 401


async def test_login_audited(db, login_as, seeded):
    await login_as("lan@demo.local")
    rows = (await db.scalars(select(AuditLog).where(AuditLog.action == "login"))).all()
    assert len(rows) == 1
    assert rows[0].user_id == seeded.users["lan@demo.local"]
