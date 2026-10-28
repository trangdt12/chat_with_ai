import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin import service
from app.admin.schemas import (
    AddMemberIn,
    AdminDocumentOut,
    AuditPageOut,
    ChangeRoleIn,
    DocSetOut,
    MemberOut,
    PurgeIn,
    PurgeOut,
)
from app.auth.deps import require_admin
from app.auth.policy import AccessContext
from app.db import get_db

# Mọi route đều yêu cầu admin. Trang quản trị không có lối tắt nào tới nội dung tài liệu (AC-US021-5).
router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


@router.get("/doc-sets")
async def list_doc_sets(db: AsyncSession = Depends(get_db)) -> list[DocSetOut]:
    return await service.list_doc_sets(db)


@router.get("/doc-sets/{dsid}/members")
async def list_members(dsid: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[MemberOut]:
    return await service.list_members(db, dsid)


@router.post("/doc-sets/{dsid}/members", status_code=201)
async def add_member(
    dsid: uuid.UUID,
    body: AddMemberIn,
    admin: AccessContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    return await service.add_member(db, admin, dsid, body.email, body.role)


@router.patch("/doc-sets/{dsid}/members/{uid}")
async def change_role(
    dsid: uuid.UUID,
    uid: uuid.UUID,
    body: ChangeRoleIn,
    admin: AccessContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> MemberOut:
    return await service.change_role(db, admin, dsid, uid, body.role)


@router.delete("/doc-sets/{dsid}/members/{uid}", status_code=204)
async def remove_member(
    dsid: uuid.UUID,
    uid: uuid.UUID,
    admin: AccessContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await service.remove_member(db, admin, dsid, uid)
    return Response(status_code=204)


@router.get("/doc-sets/{dsid}/documents")
async def list_documents(
    dsid: uuid.UUID, q: str | None = Query(default=None, max_length=200), db: AsyncSession = Depends(get_db)
) -> list[AdminDocumentOut]:
    return await service.list_admin_documents(db, dsid, q)


@router.delete("/documents/{document_id}")
async def purge_document(
    document_id: uuid.UUID,
    body: PurgeIn,
    admin: AccessContext = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> PurgeOut:
    await service.purge_document(db, admin, document_id, body.requested_by, body.reason)
    return PurgeOut(id=document_id)


@router.get("/audit-logs")
async def audit_logs(
    doc_set_id: uuid.UUID,
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> AuditPageOut:
    return await service.query_audit_logs(db, doc_set_id, date_from, date_to, user_id, action, cursor, limit)
