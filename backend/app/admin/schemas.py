import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

Role = Literal["member", "manager"]


class DocSetOut(BaseModel):
    id: uuid.UUID
    name: str
    member_count: int


class MemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: str
    role: Role
    granted_at: datetime


class AddMemberIn(BaseModel):
    email: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=320)]
    role: Role


class ChangeRoleIn(BaseModel):
    role: Role


class AdminDocumentOut(BaseModel):
    """Chỉ thông tin mô tả (BRU-007): không có nội dung, không có link mở file."""

    id: uuid.UUID
    filename: str
    pages: int | None
    size_bytes: int
    status: str
    error_code: str | None
    uploaded_by_email: str
    uploaded_at: datetime


class PurgeIn(BaseModel):
    requested_by: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class PurgeOut(BaseModel):
    id: uuid.UUID
    removed: bool = True


class AuditItemOut(BaseModel):
    id: int
    ts: datetime
    user_id: uuid.UUID | None
    user_email: str | None
    action: str
    document_id: uuid.UUID | None
    document_filename: str | None
    meta: dict | None


class AuditPageOut(BaseModel):
    items: list[AuditItemOut]
    next_cursor: str | None
