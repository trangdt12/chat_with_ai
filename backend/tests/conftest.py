"""Hạ tầng test dùng chung.

Test chạy với Postgres thật (DB `cwd_test` trên service `db`) và bật LLM/embedding giả.
Biến môi trường phải được đặt TRƯỚC khi import `app`, vì `app.db` tạo engine lúc import.
"""

import os
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path


def _test_database_url() -> str:
    if url := os.environ.get("TEST_DATABASE_URL"):
        return url
    base = os.environ.get("DATABASE_URL", "postgresql+asyncpg://cwd:cwd@db:5432/cwd")
    return base.rsplit("/", 1)[0] + "/cwd_test"


os.environ["DATABASE_URL"] = _test_database_url()
os.environ["LLM_FAKE"] = "1"
os.environ["EMBED_FAKE"] = "1"
os.environ["FILES_DIR"] = tempfile.mkdtemp(prefix="cwd-files-")

import httpx  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import select, text  # noqa: E402

from app.db import SessionLocal, engine  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base, DocSet, User  # noqa: E402
from app.seed import DOC_SET_NAME, seed  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.attributes["configure_logger"] = False
    return cfg


@pytest.fixture(scope="session", autouse=True)
def _migrate():
    """Dựng lại schema từ đầu mỗi lượt chạy test (đồng thời kiểm tra downgrade chạy được)."""
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


@pytest.fixture
async def db():
    """Session tới DB test, các bảng được dọn sạch trước mỗi test."""
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    async with SessionLocal() as session:
        yield session


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@dataclass(frozen=True)
class SeedData:
    doc_set_id: uuid.UUID
    users: dict[str, uuid.UUID]  # email → user_id


@pytest.fixture
async def seeded(db) -> SeedData:
    """Dữ liệu mẫu của app.seed: "Dự án X", Lan (member), Minh (manager), Hùng (admin), Tuấn, Anh (member)."""
    await seed(db)
    doc_set_id = await db.scalar(select(DocSet.id).where(DocSet.name == DOC_SET_NAME))
    users = dict((await db.execute(select(User.email, User.id))).all())
    return SeedData(doc_set_id=doc_set_id, users=users)


@pytest.fixture
async def login_as(app, seeded):
    """`c = await login_as("lan@demo.local")` → httpx client đã có cookie phiên của người đó."""
    clients: list[httpx.AsyncClient] = []

    async def _login(email: str) -> httpx.AsyncClient:
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        c = httpx.AsyncClient(transport=transport, base_url="http://test")
        r = await c.post("/api/v1/auth/login", json={"email": email})
        assert r.status_code == 204, r.text
        clients.append(c)
        return c

    yield _login
    for c in clients:
        await c.aclose()
