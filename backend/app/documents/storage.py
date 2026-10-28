"""Lưu file PDF trên ổ đĩa local: {files_dir}/{doc_set_id}/{document_id}.pdf."""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.config import get_settings

log = logging.getLogger(__name__)

PDF_MAGIC = b"%PDF-"
READ_CHUNK = 1024 * 1024


def file_path_for(doc_set_id: uuid.UUID, document_id: uuid.UUID) -> Path:
    return Path(get_settings().files_dir) / str(doc_set_id) / f"{document_id}.pdf"


@dataclass
class StagedFile:
    """File đã ghi ra file tạm và qua kiểm tra; `error_code` khác None thì không có file tạm."""

    tmp_path: Path | None
    size_bytes: int
    error_code: str | None = None


async def stage_upload(upload: UploadFile, doc_set_id: uuid.UUID, max_bytes: int) -> StagedFile:
    """Kiểm tra 5 byte đầu là `%PDF-` rồi ghi ra file tạm theo khối 1 MB, dừng ngay khi vượt `max_bytes`."""
    first = await upload.read(READ_CHUNK)
    if not first.startswith(PDF_MAGIC):
        return StagedFile(None, 0, "NOT_PDF")

    folder = Path(get_settings().files_dir) / str(doc_set_id)
    await asyncio.to_thread(folder.mkdir, parents=True, exist_ok=True)
    tmp_path = folder / f".upload-{uuid.uuid4()}.tmp"
    size = 0
    try:
        with open(tmp_path, "wb") as f:
            chunk = first
            while chunk:
                size += len(chunk)
                if size > max_bytes:
                    break
                await asyncio.to_thread(f.write, chunk)
                chunk = await upload.read(READ_CHUNK)
    except BaseException:
        delete_file(tmp_path)
        raise
    if size > max_bytes:
        delete_file(tmp_path)
        return StagedFile(None, size, "FILE_TOO_LARGE")
    return StagedFile(tmp_path, size)


def commit_staged(tmp_path: Path, final_path: Path) -> None:
    os.replace(tmp_path, final_path)


def delete_file(path: str | Path | None) -> None:
    """Xóa file; không có file thì bỏ qua. Lỗi khác chỉ log cảnh báo (không có nội dung)."""
    if not path:
        return
    try:
        Path(path).unlink(missing_ok=True)
    except OSError as e:
        log.warning("không xóa được file %s: %s", Path(path).name, type(e).__name__)
