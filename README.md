# Chat với tài liệu — bản thử nghiệm

Hỏi đáp có dẫn nguồn trên tài liệu dự án (PDF). Chạy local bằng Docker Compose: PostgreSQL + pgvector, FastAPI (`api`, `worker`), React (`web`), Claude qua Anthropic API.

Tài liệu: yêu cầu ở [docs/requirements](docs/requirements/UserStories.md), thiết kế ở [docs/design](docs/design), task triển khai ở [docs/implements/tasks](docs/implements/tasks/README.md).

## Chạy

```bash
cp .env.example .env          # điền ANTHROPIC_API_KEY
docker compose up             # db, api (:8000), worker, web (:5173)
docker compose exec api alembic upgrade head && docker compose exec api python -m app.seed
```

Mở http://localhost:5173 và chọn một tài khoản thử nghiệm:

| Email | Vai trò |
|---|---|
| `lan@demo.local` | Thành viên "Dự án X" |
| `minh@demo.local` | Quản lý bộ tài liệu "Dự án X" (được tải lô) |
| `hung@demo.local` | Quản trị viên, không thuộc nhóm |
| `tuan@demo.local` | Chưa thuộc nhóm nào |
| `anh@demo.local` | Thành viên "Dự án X" (dùng cho kịch bản gỡ thành viên) |

- Lần đầu worker tải model embedding `BAAI/bge-m3` (~2,2 GB) vào `./models`, nên tài liệu đầu tiên xử lý lâu.
- Chạy không tốn tiền, không tải model: đặt `LLM_FAKE=1` và `EMBED_FAKE=1` trong `.env` rồi `docker compose up -d --force-recreate api worker`.

## Kiểm thử

```bash
# Backend: pytest dùng DB cwd_test trên service db, LLM và embedding giả
docker compose exec api ruff check .
docker compose exec api pytest

# Frontend: unit test (Vitest)
docker compose exec web npm test

# End-to-end (Playwright, chạy trên máy host; backend phải bật LLM_FAKE=1, EMBED_FAKE=1)
cd web && npx playwright install chromium && npm run e2e

# Bộ câu hỏi đánh giá với Claude thật (T-15)
docker compose exec api python /eval/run_eval.py --dry-run
```

Đặt lại dữ liệu mẫu: `docker compose exec api python -m app.seed --reset`.
