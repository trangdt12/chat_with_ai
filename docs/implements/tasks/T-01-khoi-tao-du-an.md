# T-01 · Khởi tạo dự án, Docker Compose, cấu hình

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| Nền tảng | — | 1 ngày |

## 1. Mục tiêu
Clone repo, điền `ANTHROPIC_API_KEY`, chạy `docker compose up` là có đủ `db`, `api`, `worker`, `web` chạy được. Mọi task sau xây trên khung này.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `docker-compose.yml` | 4 service: `db` (`pgvector/pgvector:pg16`, volume `pgdata`), `api` (uvicorn `app.main:app --reload --workers 1`, cổng 8000; **chỉ 1 tiến trình** vì nút Dừng của T-10 dùng registry trong bộ nhớ), `worker` (`python -m app.ingestion.worker`), `web` (Vite, cổng 5173). `api`/`worker` mount `./backend`, `./data/files`, `./models` (cache model embedding) |
| `.env.example` | `DATABASE_URL=postgresql+asyncpg://cwd:cwd@db:5432/cwd`, `ANTHROPIC_API_KEY=`, `FILES_DIR=/data/files`, `HF_HOME=/models` |
| `backend/pyproject.toml` | fastapi, uvicorn[standard], sqlalchemy[asyncio], asyncpg, alembic, pydantic-settings, python-multipart, pypdf, pgvector, sentence-transformers, anthropic, sse-starlette; dev: pytest, pytest-asyncio, httpx, ruff |
| `backend/Dockerfile` | `python:3.12-slim`, cài dependency, `WORKDIR /app` |
| `backend/app/config.py` | `Settings(BaseSettings)` với đủ khóa ở README §2.5 (gồm `llm_fake`, `embed_fake` cho test); `get_settings()` có `lru_cache` |
| `backend/app/db.py` | `engine = create_async_engine(settings.database_url)`, `SessionLocal`, `async def get_db() -> AsyncIterator[AsyncSession]` |
| `backend/app/errors.py` | `AppError` + handler trả `{"code","message"}` |
| `backend/app/main.py` | `create_app()`: handler lỗi, `GET /api/v1/health` → `{"status":"ok"}` (kiểm tra `SELECT 1`), chỗ gắn router các module |
| `backend/app/{auth,documents,ingestion,qa,admin}/__init__.py` | Thư mục rỗng theo README §2.1 |
| `backend/app/ingestion/worker.py` | Tạm thời: vòng lặp log "worker started", ngủ `worker_poll_seconds` (T-06 thay nội dung) |
| `web/` | `npm create vite` (react-ts), thêm `@tanstack/react-query`, `react-router-dom`, `react-markdown`; `vite.config.ts` proxy `/api` → `http://api:8000` |
| `web/src/styles/tokens.css` | Chép biến màu, font, khoảng cách từ `docs/design/UI_UX_design/assets` |
| `README.md` (gốc repo) | Cách chạy (3 lệnh ở README task §1), cách chạy test |

### 2.2 Chi tiết
```python
# app/errors.py
class AppError(Exception):
    def __init__(self, code: str, status: int, message: str = ""): ...

async def app_error_handler(request, exc: AppError) -> JSONResponse:
    return JSONResponse({"code": exc.code, "message": exc.message}, status_code=exc.status)
```
- Lỗi validation của FastAPI (`RequestValidationError`) cũng trả dạng `{"code": "VALIDATION_ERROR", "message": ...}` với status 422.
- Lỗi không bắt được → 500 `{"code": "INTERNAL"}`; log stacktrace nhưng không log body request.
- Logging: `logging.basicConfig(level=INFO)`, định dạng một dòng. Không log body hay nội dung câu hỏi (README §2.6).

## 3. Tiêu chí hoàn thành
- [ ] Cho trước máy có Docker; khi chạy `docker compose up`; thì `GET http://localhost:8000/api/v1/health` trả `{"status":"ok"}` và `http://localhost:5173` hiện trang React.
- [ ] Cho trước Vite đang chạy; khi frontend gọi `/api/v1/health`; thì request đi qua proxy, không lỗi CORS.
- [ ] Cho trước `ruff check` và `pytest`; khi chạy trong container `api`; thì cả hai chạy được (dù chưa có test nghiệp vụ).
- [ ] `config.py` có đủ khóa ở README §2.5; đổi biến môi trường thì giá trị đổi theo.

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `tests/test_health.py::test_health_ok` | 200, `{"status":"ok"}` |
| `tests/test_errors.py::test_app_error_shape` | Route ném `AppError("FORBIDDEN", 403)` → body `{"code":"FORBIDDEN",...}` |
| `tests/test_errors.py::test_validation_error_shape` | Body sai kiểu → 422 `VALIDATION_ERROR` |

`tests/conftest.py` dựng app với DB test (`DATABASE_URL` trỏ tới DB `cwd_test` trên service `db`) và `httpx.AsyncClient`.

## 5. Ghi chú
- Model `bge-m3` (~2 GB) được tải lần đầu khi worker chạy T-06; mount `./models` để không tải lại.
- Không làm CI, Terraform, observability (README §4).
- Khi làm: thêm `tests/test_config.py` cho tiêu chí "đổi biến môi trường thì giá trị đổi theo"; Vitest bật `passWithNoTests` để `npm test` không lỗi khi chưa có test frontend; ruff khai báo `alembic` là third-party (vì có thư mục `backend/alembic/`). DB `cwd_test` chỉ được tạo khi volume `pgdata` còn trống, xem README gốc nếu cần tạo tay.
