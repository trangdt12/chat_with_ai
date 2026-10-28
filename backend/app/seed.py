"""Dữ liệu mẫu: bộ tài liệu "Dự án X" và các tài khoản đăng nhập thử.

`python -m app.seed` chạy lại bao nhiêu lần cũng được (so theo email / tên).
`python -m app.seed --reset` xóa sạch dữ liệu và file đã tải lên rồi seed lại (dùng cho e2e và demo).
"""

import argparse
import asyncio
import logging
import shutil
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal, engine
from app.models import Base, DocSet, Membership, User

log = logging.getLogger("app.seed")

DOC_SET_NAME = "Dự án X"

# (email, tên hiển thị, is_admin, vai trò trong "Dự án X" hoặc None)
SEED_USERS: tuple[tuple[str, str, bool, str | None], ...] = (
    ("lan@demo.local", "Nguyễn Thị Lan", False, "member"),
    ("minh@demo.local", "Trần Văn Minh", False, "manager"),
    ("hung@demo.local", "Phạm Văn Hùng", True, None),
    ("tuan@demo.local", "Lê Minh Tuấn", False, None),
    # Dùng cho kịch bản gỡ thành viên (T-13, T-15).
    ("anh@demo.local", "Phạm Đức Anh", False, "member"),
)


async def reset(db: AsyncSession) -> None:
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    await db.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    files_dir = Path(get_settings().files_dir)
    if files_dir.is_dir():
        for child in files_dir.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()


async def seed(db: AsyncSession) -> None:
    doc_set = await db.scalar(select(DocSet).where(DocSet.name == DOC_SET_NAME))
    if doc_set is None:
        doc_set = DocSet(name=DOC_SET_NAME)
        db.add(doc_set)
        await db.flush()

    for email, display_name, is_admin, role in SEED_USERS:
        user = await db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(email=email, display_name=display_name, is_admin=is_admin)
            db.add(user)
            await db.flush()
        if role is not None and await db.get(Membership, (doc_set.id, user.id)) is None:
            db.add(Membership(doc_set_id=doc_set.id, user_id=user.id, role=role))

    await db.commit()


async def main(do_reset: bool) -> None:
    async with SessionLocal() as db:
        if do_reset:
            await reset(db)
        await seed(db)
    await engine.dispose()
    log.info("seed xong: %d tài khoản, bộ tài liệu %r", len(SEED_USERS), DOC_SET_NAME)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Tạo dữ liệu mẫu")
    parser.add_argument("--reset", action="store_true", help="xóa toàn bộ dữ liệu và file trước khi seed")
    asyncio.run(main(parser.parse_args().reset))
