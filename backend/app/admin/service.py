"""Quản trị: nhóm truy cập và vai trò (T-13), gỡ tài liệu và nhật ký truy cập (T-14).

Quyền đọc từ DB ở mỗi request nên gỡ thành viên có hiệu lực ngay ở request kế tiếp của người đó.
`meta` của audit chỉ chứa id và vai trò — không chứa email hay nội dung.
"""

import logging
import uuid
from datetime import UTC, date, datetime, time, timedelta, timezone

from sqlalchemy import and_, delete, func, or_, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.schemas import AdminDocumentOut, AuditItemOut, AuditPageOut, DocSetOut, MemberOut
from app.audit import record_audit
from app.auth.policy import AccessContext
from app.documents import storage
from app.errors import AppError
from app.models import AUDIT_ACTIONS, AuditLog, Citation, DocSet, Document, Membership, User

log = logging.getLogger(__name__)

# Ngày lọc nhật ký tính theo giờ Việt Nam (UTC+7, không có giờ mùa hè).
LOCAL_TZ = timezone(timedelta(hours=7))
AUDIT_DEFAULT_DAYS = 7


def not_found() -> AppError:
    return AppError("NOT_FOUND", 404, "Không tìm thấy")


async def _require_doc_set(db: AsyncSession, dsid: uuid.UUID) -> DocSet:
    doc_set = await db.get(DocSet, dsid)
    if doc_set is None:
        raise not_found()
    return doc_set


# ---------------------------------------------------------------- T-13 nhóm truy cập


async def list_doc_sets(db: AsyncSession) -> list[DocSetOut]:
    rows = await db.execute(
        select(DocSet.id, DocSet.name, func.count(Membership.user_id))
        .outerjoin(Membership, Membership.doc_set_id == DocSet.id)
        .group_by(DocSet.id)
        .order_by(DocSet.name)
    )
    return [DocSetOut(id=i, name=n, member_count=c) for i, n, c in rows.all()]


def _member_out(user: User, m: Membership) -> MemberOut:
    return MemberOut(
        user_id=user.id, email=user.email, display_name=user.display_name, role=m.role, granted_at=m.granted_at
    )


async def list_members(db: AsyncSession, dsid: uuid.UUID) -> list[MemberOut]:
    await _require_doc_set(db, dsid)
    rows = await db.execute(
        select(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.doc_set_id == dsid)
        .order_by(Membership.granted_at, User.display_name)
    )
    return [_member_out(u, m) for u, m in rows.all()]


async def add_member(db: AsyncSession, admin: AccessContext, dsid: uuid.UUID, email: str, role: str) -> MemberOut:
    await _require_doc_set(db, dsid)
    user = await db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))
    if user is None:
        raise AppError("USER_NOT_FOUND", 404, "Không tìm thấy tài khoản này trong hệ thống")
    if await db.get(Membership, (dsid, user.id)) is not None:
        raise AppError("ALREADY_MEMBER", 409, "Tài khoản này đã thuộc nhóm")
    m = Membership(doc_set_id=dsid, user_id=user.id, role=role)
    db.add(m)
    await record_audit(db, admin.user_id, "member_add", dsid, meta={"target_user_id": str(user.id), "role": role})
    await db.commit()
    await db.refresh(m)
    return _member_out(user, m)


async def _get_membership(db: AsyncSession, dsid: uuid.UUID, uid: uuid.UUID) -> tuple[User, Membership]:
    await _require_doc_set(db, dsid)
    m = await db.get(Membership, (dsid, uid))
    if m is None:
        raise not_found()
    return await db.get(User, uid), m


async def change_role(db: AsyncSession, admin: AccessContext, dsid: uuid.UUID, uid: uuid.UUID, role: str) -> MemberOut:
    user, m = await _get_membership(db, dsid, uid)
    previous = m.role
    m.role = role
    meta = {"target_user_id": str(uid), "from": previous, "to": role}
    await record_audit(db, admin.user_id, "role_change", dsid, meta=meta)
    await db.commit()
    return _member_out(user, m)


async def remove_member(db: AsyncSession, admin: AccessContext, dsid: uuid.UUID, uid: uuid.UUID) -> None:
    await _get_membership(db, dsid, uid)
    await db.execute(delete(Membership).where(Membership.doc_set_id == dsid, Membership.user_id == uid))
    await record_audit(db, admin.user_id, "member_remove", dsid, meta={"target_user_id": str(uid)})
    await db.commit()


# ---------------------------------------------------------------- T-14 gỡ tài liệu


def _escape_like(q: str) -> str:
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def list_admin_documents(db: AsyncSession, dsid: uuid.UUID, q: str | None) -> list[AdminDocumentOut]:
    await _require_doc_set(db, dsid)
    stmt = (
        select(Document, User.email)
        .join(User, User.id == Document.uploaded_by)
        .where(Document.doc_set_id == dsid)
        .order_by(Document.uploaded_at.desc(), Document.id)
    )
    if q and q.strip():
        stmt = stmt.where(Document.filename.ilike(f"%{_escape_like(q.strip())}%", escape="\\"))
    rows = await db.execute(stmt)
    return [
        AdminDocumentOut(
            id=d.id,
            filename=d.filename,
            pages=d.pages,
            size_bytes=d.size_bytes,
            status=d.status,
            error_code=d.error_code,
            uploaded_by_email=email,
            uploaded_at=d.uploaded_at,
        )
        for d, email in rows.all()
    ]


async def purge_document(
    db: AsyncSession, admin: AccessContext, document_id: uuid.UUID, requested_by: str, reason: str
) -> None:
    """Gỡ hoàn toàn: file gốc, đoạn văn + embedding (ON DELETE CASCADE), đoạn trích trong lịch sử hội thoại."""
    doc = await db.get(Document, document_id, with_for_update=True)  # worker (T-06) chờ hoặc thấy đã bị gỡ
    if doc is None:
        raise not_found()
    file_path, doc_set_id, pages = doc.file_path, doc.doc_set_id, doc.pages
    await db.execute(
        update(Citation)
        .where(Citation.document_id == doc.id)
        .values(snippet=None, filename=None, chunk_id=None, removed=True)
    )
    await db.delete(doc)
    meta = {"requested_by": requested_by, "reason": reason, "pages": pages}
    await record_audit(db, admin.user_id, "remove_document", doc_set_id, document_id, meta=meta)
    await db.commit()
    # Sau commit: lỗi xóa file chỉ log cảnh báo (không có nội dung), không rollback.
    storage.delete_file(file_path)


# ---------------------------------------------------------------- T-14 nhật ký


def _parse_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        ts, _, ident = cursor.partition("|")
        return datetime.fromisoformat(ts), int(ident)
    except ValueError as e:
        raise AppError("VALIDATION_ERROR", 422, "cursor không hợp lệ") from e


async def query_audit_logs(
    db: AsyncSession,
    doc_set_id: uuid.UUID,
    date_from: date | None,
    date_to: date | None,
    user_id: uuid.UUID | None,
    action: str | None,
    cursor: str | None,
    limit: int,
) -> AuditPageOut:
    """Không ghi audit cho chính thao tác tra cứu."""
    await _require_doc_set(db, doc_set_id)
    if action is not None and action not in AUDIT_ACTIONS:
        raise AppError("VALIDATION_ERROR", 422, "Thao tác không hợp lệ")

    date_to = date_to or datetime.now(LOCAL_TZ).date()
    date_from = date_from or date_to - timedelta(days=AUDIT_DEFAULT_DAYS - 1)
    start = datetime.combine(date_from, time.min, LOCAL_TZ).astimezone(UTC)
    end = datetime.combine(date_to + timedelta(days=1), time.min, LOCAL_TZ).astimezone(UTC)  # `to` tính hết ngày

    # Đăng nhập không gắn bộ tài liệu: hiện các lần đăng nhập của thành viên hiện tại của bộ.
    members = select(Membership.user_id).where(Membership.doc_set_id == doc_set_id)
    scope = or_(
        AuditLog.doc_set_id == doc_set_id,
        and_(AuditLog.doc_set_id.is_(None), AuditLog.action == "login", AuditLog.user_id.in_(members)),
    )
    stmt = (
        select(AuditLog, User.email, Document.filename)
        .outerjoin(User, User.id == AuditLog.user_id)
        .outerjoin(Document, Document.id == AuditLog.document_id)  # tài liệu đã gỡ → filename null
        .where(scope, AuditLog.ts >= start, AuditLog.ts < end)
        .order_by(AuditLog.ts.desc(), AuditLog.id.desc())
        .limit(limit + 1)
    )
    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if cursor:
        ts, ident = _parse_cursor(cursor)
        stmt = stmt.where(tuple_(AuditLog.ts, AuditLog.id) < tuple_(ts, ident))

    rows = (await db.execute(stmt)).all()
    items = [
        AuditItemOut(
            id=a.id,
            ts=a.ts,
            user_id=a.user_id,
            user_email=email,
            action=a.action,
            document_id=a.document_id,
            document_filename=filename,
            meta=a.meta,
        )
        for a, email, filename in rows[:limit]
    ]
    next_cursor = f"{items[-1].ts.isoformat()}|{items[-1].id}" if len(rows) > limit else None
    return AuditPageOut(items=items, next_cursor=next_cursor)
