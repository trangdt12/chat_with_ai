import uuid

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.policy import AccessContext, can_admin, can_batch_upload, can_use_content
from app.db import get_db
from app.errors import AppError

SESSION_COOKIE = "cwd_session"

# Thông báo 403 không chứa tên bộ tài liệu hay tên file (AC-US013-1).
FORBIDDEN_MESSAGE = "Bạn không có quyền thực hiện thao tác này"


def unauthenticated() -> AppError:
    return AppError("UNAUTHENTICATED", 401, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn")


def forbidden(message: str = FORBIDDEN_MESSAGE) -> AppError:
    return AppError("FORBIDDEN", 403, message)


async def current_ctx(request: Request, db: AsyncSession = Depends(get_db)) -> AccessContext:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise unauthenticated()
    ctx = await service.load_context(db, token)
    if ctx is None:
        raise unauthenticated()
    return ctx


def ensure_member(ctx: AccessContext, dsid: uuid.UUID) -> None:
    if not can_use_content(ctx, dsid):
        raise forbidden()


async def require_member(dsid: uuid.UUID, ctx: AccessContext = Depends(current_ctx)) -> AccessContext:
    ensure_member(ctx, dsid)
    return ctx


async def require_manager(dsid: uuid.UUID, ctx: AccessContext = Depends(current_ctx)) -> AccessContext:
    if not can_batch_upload(ctx, dsid):
        raise forbidden()
    return ctx


async def require_admin(ctx: AccessContext = Depends(current_ctx)) -> AccessContext:
    if not can_admin(ctx):
        raise forbidden()
    return ctx
