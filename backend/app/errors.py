import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, code: str, status: int, message: str = ""):
        super().__init__(code)
        self.code = code
        self.status = status
        self.message = message


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse({"code": exc.code, "message": exc.message}, status_code=exc.status)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Chỉ trả vị trí và loại lỗi, không trả lại giá trị người dùng gửi lên.
    fields = [".".join(str(p) for p in e.get("loc", ())) for e in exc.errors()]
    message = "Dữ liệu không hợp lệ: " + ", ".join(fields) if fields else "Dữ liệu không hợp lệ"
    return JSONResponse({"code": "VALIDATION_ERROR", "message": message}, status_code=422)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse({"code": "INTERNAL", "message": "Lỗi hệ thống"}, status_code=500)
