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

# End-to-end (Playwright, chạy trên máy host; backend phải bật LLM_FAKE=1, EMBED_FAKE=1
# và nên đặt RETRIEVAL_NOT_FOUND_TAU=0.25 vì embedding giả cho cosine thấp hơn bge-m3)
# Mỗi spec tự đặt lại dữ liệu bằng `docker compose exec -T api python -m app.seed --reset`
cd web && npm install && npx playwright install chromium && npm run e2e

# Bộ câu hỏi đánh giá với Claude thật (T-15): sinh PDF mẫu, kiểm tra, rồi chạy (~20–30 lần gọi Claude)
cd web && npm run eval:corpus && cd ..
docker compose exec api python /eval/run_eval.py --dry-run
docker compose exec api python /eval/run_eval.py          # báo cáo ở eval/reports/YYYY-MM-DD.md
```

- Kịch bản demo 15 phút: [docs/implements/demo-script.md](docs/implements/demo-script.md).
- Thử Claude thật không cần giao diện: `docker compose exec api python -m app.qa.llm_smoke`.

DB test `cwd_test` được tạo bởi `backend/docker/initdb/` **chỉ khi volume `pgdata` còn trống**. Nếu volume đã có từ trước (pytest báo `database "cwd_test" does not exist`), tạo tay một lần:

```bash
docker compose exec db psql -U cwd -d cwd -c "CREATE DATABASE cwd_test OWNER cwd"
```

Đặt lại dữ liệu mẫu: `docker compose exec api python -m app.seed --reset`.
