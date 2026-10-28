"""Bảng quyền README §2.4. Hàm thuần, không I/O."""

import uuid
from dataclasses import dataclass
from typing import Literal

Role = Literal["member", "manager"]


@dataclass(frozen=True)
class AccessContext:
    user_id: uuid.UUID
    is_admin: bool
    memberships: dict[uuid.UUID, Role]  # doc_set_id → role, đọc từ DB ở MỖI request
    session_id_hash: str


def can_use_content(ctx: AccessContext, dsid: uuid.UUID) -> bool:
    """Xem danh sách, trích dẫn, file gốc; hỏi đáp; tải 1 file. Admin không thuộc nhóm thì không có (BRU-007)."""
    return dsid in ctx.memberships


def can_batch_upload(ctx: AccessContext, dsid: uuid.UUID) -> bool:
    return ctx.memberships.get(dsid) == "manager"


def can_view_metadata(ctx: AccessContext, dsid: uuid.UUID) -> bool:
    return dsid in ctx.memberships or ctx.is_admin


def can_admin(ctx: AccessContext) -> bool:
    return ctx.is_admin
