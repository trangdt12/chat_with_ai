from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import service
from app.auth.deps import SESSION_COOKIE, current_ctx
from app.auth.policy import AccessContext
from app.db import get_db

router = APIRouter()


class LoginIn(BaseModel):
    email: str


@router.get("/auth/dev-users")
async def dev_users(db: AsyncSession = Depends(get_db)) -> list[dict]:
    return [{"email": u.email, "display_name": u.display_name} for u in await service.list_dev_users(db)]


@router.post("/auth/login", status_code=204)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)) -> Response:
    token = await service.login(db, body.email)
    resp = Response(status_code=204)
    resp.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", path="/")
    return resp


@router.post("/auth/logout", status_code=204)
async def logout(request: Request, db: AsyncSession = Depends(get_db)) -> Response:
    if token := request.cookies.get(SESSION_COOKIE):
        await service.logout(db, token)
    resp = Response(status_code=204)
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@router.get("/me")
async def me(ctx: AccessContext = Depends(current_ctx), db: AsyncSession = Depends(get_db)) -> dict:
    return await service.get_me(db, ctx)
