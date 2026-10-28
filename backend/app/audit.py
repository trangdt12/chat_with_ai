import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def record_audit(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    action: str,
    doc_set_id: uuid.UUID | None,
    document_id: uuid.UUID | None = None,
    meta: dict | None = None,
) -> None:
    """Thêm một dòng nhật ký vào transaction hiện tại (người gọi tự commit).

    `meta` chỉ chứa id, số đếm, mã trạng thái — KHÔNG chứa câu hỏi, câu trả lời, đoạn văn hay tên file.
    """
    db.add(AuditLog(user_id=user_id, action=action, doc_set_id=doc_set_id, document_id=document_id, meta=meta))
