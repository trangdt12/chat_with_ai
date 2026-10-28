from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

# hide_parameters: thông báo lỗi SQL không kèm giá trị tham số (có thể là nội dung tài liệu, câu hỏi).
engine = create_async_engine(get_settings().database_url, pool_pre_ping=True, hide_parameters=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
