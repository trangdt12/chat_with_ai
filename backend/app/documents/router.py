import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import current_ctx, require_member
from app.auth.policy import AccessContext
from app.db import get_db
from app.documents import service
from app.documents.schemas import ClassificationOut, DocumentOut, UploadResult

router = APIRouter()


@router.post("/doc-sets/{dsid}/classification-confirmations", status_code=201)
async def confirm_classification(
    dsid: uuid.UUID, ctx: AccessContext = Depends(require_member), db: AsyncSession = Depends(get_db)
) -> ClassificationOut:
    return ClassificationOut(confirmed_at=await service.confirm_classification(db, ctx, dsid))


@router.post("/doc-sets/{dsid}/documents")
async def upload_documents(
    dsid: uuid.UUID,
    files: list[UploadFile] = File(...),
    ctx: AccessContext = Depends(require_member),
    db: AsyncSession = Depends(get_db),
) -> list[UploadResult]:
    return await service.upload_documents(db, ctx, dsid, files)


@router.get("/doc-sets/{dsid}/documents")
async def list_documents(
    dsid: uuid.UUID, ctx: AccessContext = Depends(require_member), db: AsyncSession = Depends(get_db)
) -> list[DocumentOut]:
    return await service.list_documents(db, ctx, dsid)


@router.get("/documents/{document_id}/file")
async def open_file(
    document_id: uuid.UUID, ctx: AccessContext = Depends(current_ctx), db: AsyncSession = Depends(get_db)
) -> FileResponse:
    # Tham số ?page=N chỉ để FE ghép #page=N vào URL; server bỏ qua.
    doc = await service.open_file(db, ctx, document_id)
    return FileResponse(
        doc.file_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{quote(doc.filename)}"},
    )
