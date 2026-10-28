import os
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import UploadFile
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.auth.deps import ensure_member, forbidden
from app.auth.policy import AccessContext, can_batch_upload
from app.config import get_settings
from app.documents import storage
from app.documents.schemas import DocumentOut, UploadResult
from app.errors import AppError
from app.models import AuditLog, DocSet, Document, Session, User

BATCH_FORBIDDEN_MESSAGE = "Chỉ Quản lý bộ tài liệu được tải nhiều file một lần. Vui lòng tải từng file."
VIEW_LIST_AUDIT_INTERVAL = timedelta(minutes=1)


def document_removed() -> AppError:
    return AppError("DOCUMENT_REMOVED", 410, "Tài liệu đã được gỡ khỏi bộ tài liệu")


async def confirm_classification(db: AsyncSession, ctx: AccessContext, dsid: uuid.UUID) -> datetime:
    sess = await db.get(Session, ctx.session_id_hash)
    now = datetime.now(UTC)
    sess.classification_confirmed_at = now
    await record_audit(db, ctx.user_id, "classification_confirm", dsid)
    await db.commit()
    return now


def clean_filename(raw: str | None) -> str:
    name = (raw or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not name:
        return "tai-lieu.pdf"
    if len(name) > 200:
        stem, ext = os.path.splitext(name)
        name = stem[: 200 - len(ext)] + ext
    return name


def unique_filename(name: str, existing: set[str]) -> str:
    """Trùng tên (E-09): `Ten.pdf` → `Ten (2).pdf`, `Ten (3).pdf`, …"""
    if name not in existing:
        return name
    stem, ext = os.path.splitext(name)
    n = 2
    while f"{stem} ({n}){ext}" in existing:
        n += 1
    return f"{stem} ({n}){ext}"


async def upload_documents(
    db: AsyncSession, ctx: AccessContext, dsid: uuid.UUID, files: list[UploadFile]
) -> list[UploadResult]:
    settings = get_settings()
    ensure_member(ctx, dsid)
    if len(files) > 1 and not can_batch_upload(ctx, dsid):
        raise forbidden(BATCH_FORBIDDEN_MESSAGE)
    if len(files) > settings.doc_set_max_documents:
        raise AppError(
            "VALIDATION_ERROR", 422, f"Mỗi lần tải tối đa {settings.doc_set_max_documents} file"
        )
    sess = await db.get(Session, ctx.session_id_hash)
    if sess is None or sess.classification_confirmed_at is None:
        raise AppError("CLASSIFICATION_REQUIRED", 409, "Cần xác nhận phân loại tài liệu trước khi tải lên")
    await db.rollback()  # không giữ transaction mở trong lúc nhận file

    results: list[UploadResult] = []
    for upload in files:
        name = clean_filename(upload.filename)
        staged = await storage.stage_upload(upload, dsid, settings.upload_max_bytes)
        if staged.error_code:
            results.append(UploadResult(filename=name, error_code=staged.error_code))
            continue
        try:
            results.append(await _register(db, ctx, dsid, name, staged))
        finally:
            storage.delete_file(staged.tmp_path)  # đã os.replace thì file tạm không còn — bỏ qua
    return results


async def _register(
    db: AsyncSession, ctx: AccessContext, dsid: uuid.UUID, name: str, staged: storage.StagedFile
) -> UploadResult:
    """Một transaction ngắn cho mỗi file: khóa dòng doc_sets để đếm số tài liệu an toàn khi tải đồng thời."""
    await db.execute(select(DocSet.id).where(DocSet.id == dsid).with_for_update())
    existing = set(await db.scalars(select(Document.filename).where(Document.doc_set_id == dsid)))
    if len(existing) >= get_settings().doc_set_max_documents:
        await db.rollback()
        return UploadResult(filename=name, error_code="DOC_SET_FULL")

    filename = unique_filename(name, existing)
    doc_id = uuid.uuid4()
    path = storage.file_path_for(dsid, doc_id)
    db.add(
        Document(
            id=doc_id,
            doc_set_id=dsid,
            filename=filename,
            size_bytes=staged.size_bytes,
            status="uploaded",
            progress=0,
            file_path=str(path),
            uploaded_by=ctx.user_id,
        )
    )
    await record_audit(db, ctx.user_id, "upload", dsid, doc_id, meta={"size_bytes": staged.size_bytes})
    # Đưa file vào chỗ trước khi commit để worker không bao giờ thấy tài liệu thiếu file.
    storage.commit_staged(staged.tmp_path, path)
    try:
        await db.commit()
    except BaseException:
        storage.delete_file(path)
        raise
    return UploadResult(filename=filename, id=doc_id, status="uploaded")


async def list_documents(db: AsyncSession, ctx: AccessContext, dsid: uuid.UUID) -> list[DocumentOut]:
    ensure_member(ctx, dsid)
    rows = await db.execute(
        select(Document, User.display_name)
        .join(User, User.id == Document.uploaded_by)
        .where(Document.doc_set_id == dsid)
        .order_by(Document.uploaded_at.desc(), Document.id)
    )
    out = [
        DocumentOut(
            id=d.id,
            filename=d.filename,
            pages=d.pages,
            size_bytes=d.size_bytes,
            status=d.status,
            progress=d.progress,
            error_code=d.error_code,
            uploaded_by=uploader,
            uploaded_at=d.uploaded_at,
        )
        for d, uploader in rows.all()
    ]

    # FE polling 3 giây/lần: chỉ ghi view_list tối đa 1 lần/phút/người để không làm đầy nhật ký.
    recent = await db.scalar(
        select(
            exists().where(
                AuditLog.user_id == ctx.user_id,
                AuditLog.action == "view_list",
                AuditLog.doc_set_id == dsid,
                AuditLog.ts > datetime.now(UTC) - VIEW_LIST_AUDIT_INTERVAL,
            )
        )
    )
    if not recent:
        await record_audit(db, ctx.user_id, "view_list", dsid)
        await db.commit()
    return out


async def open_file(db: AsyncSession, ctx: AccessContext, document_id: uuid.UUID) -> Document:
    doc = await db.get(Document, document_id)
    if doc is None:
        raise document_removed()
    ensure_member(ctx, doc.doc_set_id)
    if not os.path.exists(doc.file_path):
        raise document_removed()
    await record_audit(db, ctx.user_id, "view_file", doc.doc_set_id, doc.id)
    await db.commit()
    return doc
