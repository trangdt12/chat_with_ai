import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.auth.policy import AccessContext
from app.config import get_settings
from app.errors import AppError
from app.models import DocSet, Membership, Session, User


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def login(db: AsyncSession, email: str) -> str:
    """Đăng nhập giả lập: trả token bản rõ để đặt cookie; DB chỉ lưu SHA-256 của token."""
    user = await db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise AppError("USER_NOT_FOUND", 404, "Không tìm thấy tài khoản")
    token = secrets.token_urlsafe(32)
    db.add(Session(id_hash=hash_token(token), user_id=user.id))
    await record_audit(db, user.id, "login", None)
    await db.commit()
    return token


async def logout(db: AsyncSession, token: str) -> None:
    await db.execute(delete(Session).where(Session.id_hash == hash_token(token)))
    await db.commit()


async def load_context(db: AsyncSession, token: str) -> AccessContext | None:
    """Đọc phiên + quyền từ DB (không cache). None nếu phiên không tồn tại hoặc đã hết hạn."""
    id_hash = hash_token(token)
    sess = await db.get(Session, id_hash)
    if sess is None:
        return None
    now = datetime.now(UTC)
    if now - sess.last_seen_at > timedelta(hours=get_settings().session_idle_hours):
        return None
    sess.last_seen_at = now

    user = await db.get(User, sess.user_id)
    rows = await db.execute(select(Membership.doc_set_id, Membership.role).where(Membership.user_id == user.id))
    ctx = AccessContext(
        user_id=user.id,
        is_admin=user.is_admin,
        memberships={dsid: role for dsid, role in rows.all()},
        session_id_hash=id_hash,
    )
    await db.commit()
    return ctx


async def get_me(db: AsyncSession, ctx: AccessContext) -> dict:
    user = await db.get(User, ctx.user_id)
    rows = await db.execute(
        select(DocSet.id, DocSet.name, Membership.role)
        .join(Membership, Membership.doc_set_id == DocSet.id)
        .where(Membership.user_id == ctx.user_id)
        .order_by(DocSet.name)
    )
    return {
        "user_id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "is_admin": user.is_admin,
        "doc_sets": [{"id": i, "name": n, "role": r} for i, n, r in rows.all()],
    }


async def list_dev_users(db: AsyncSession) -> list[User]:
    return list(await db.scalars(select(User).order_by(User.display_name)))

