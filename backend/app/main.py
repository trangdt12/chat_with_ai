import logging

from fastapi import APIRouter, Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.errors import AppError, app_error_handler, unhandled_error_handler, validation_error_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

API_PREFIX = "/api/v1"

health_router = APIRouter()


@health_router.get("/health")
async def health(db: AsyncSession = Depends(get_db)) -> dict:
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}


def create_app() -> FastAPI:
    app = FastAPI(title="Chat với tài liệu", openapi_url=f"{API_PREFIX}/openapi.json")
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.include_router(health_router, prefix=API_PREFIX)
    # Router các module được gắn ở đây (T-03, T-05, T-07, T-10, T-13, T-14).
    return app


app = create_app()
