"""Hạ tầng test dùng chung.

Test chạy với Postgres thật (DB `cwd_test` trên service `db`) và bật LLM/embedding giả.
Biến môi trường phải được đặt TRƯỚC khi import `app`, vì `app.db` tạo engine lúc import.
"""

import os
import tempfile


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

from app.main import create_app  # noqa: E402


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
