import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class UploadResult(BaseModel):
    filename: str  # tên sau khi đổi (nếu trùng)
    id: uuid.UUID | None = None
    status: Literal["uploaded"] | None = None
    error_code: str | None = None  # NOT_PDF | FILE_TOO_LARGE | DOC_SET_FULL


class ClassificationOut(BaseModel):
    confirmed_at: datetime


class DocumentOut(BaseModel):
    id: uuid.UUID
    filename: str
    pages: int | None
    size_bytes: int
    status: str
    progress: int
    error_code: str | None
    uploaded_by: str
    uploaded_at: datetime
