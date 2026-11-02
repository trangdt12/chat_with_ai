# Chat với tài liệu — bản thử nghiệm

Hỏi đáp có dẫn nguồn trên tài liệu dự án (PDF). Chạy local bằng Docker Compose: PostgreSQL + pgvector, FastAPI (`api`, `worker`), React (`web`), Claude qua Anthropic API.

Tài liệu: yêu cầu ở [docs/requirements](docs/requirements/UserStories.md), thiết kế ở [docs/design](docs/design), task triển khai ở [docs/implements/tasks](docs/implements/tasks/README.md).

## Kiểm thử chu kỳ 1 — đối chiếu yêu cầu

| Yêu cầu | Ở đâu |
|---|---|
| Test plan đủ 8 mục | [docs/test-plan.md](docs/test-plan.md) |
| Test case, ma trận AC ↔ TC, định nghĩa PASS/FAIL viết trước khi chạy | [docs/test-cases.md](docs/test-cases.md) (sinh từ [docs/test/test-cases.yaml](docs/test/test-cases.yaml); lịch sử git cho thấy định nghĩa được commit trước lượt chạy) |
| 100% AC của US-001, US-009 có TC; không TC nào thiếu AC | [docs/test-cases.md](docs/test-cases.md) §2, dòng "Kiểm tra độ phủ (máy)" |
| Chạy toàn bộ TC bằng Playwright trong CI | [.github/workflows/tests.yml](.github/workflows/tests.yml) → [scripts/run-tests.sh](scripts/run-tests.sh) |
| Bằng chứng: trace, log, ảnh chụp | [playwright-report/](playwright-report/) (HTML có trace, ảnh, video) · [reports/](reports/) (log, junit, môi trường) — xem ghi chú bên dưới |
| Mọi FAIL có bug ticket; PASS lặp lại ≥ 2 lần | [docs/bugs/](docs/bugs/) · 2 lượt `run-1`, `run-2` trên cùng commit, Playwright `--repeat-each=3` |
| Truy vết US ↔ AC ↔ TC ↔ bằng chứng | [docs/traceability.md](docs/traceability.md) |

**Trace, ảnh chụp, video thô của từng test** nằm trong `playwright-report/<lượt>/data/`: `*.zip` là trace, `*.png` là ảnh chụp, `*.webm` là video. Xem bằng cách mở `playwright-report/<lượt>/index.html`, chọn một test, rồi xem mục Attachments. Muốn xem một trace riêng thì chạy `cd web && npx playwright show-trace ../playwright-report/<lượt>/data/<file>.zip`.

Thư mục `test-results/` (`outputDir` của Playwright) không được đưa vào repo vì hai lý do. Thứ nhất, Playwright xóa thư mục này ở mỗi lần chạy, nên nó chỉ giữ dữ liệu của lượt cuối cùng. Thứ hai, mọi file trong đó đã được chép vào `playwright-report/<lượt>/data/`.

Cấu trúc thư mục:

```
.github/workflows/tests.yml   CI: 2 lượt độc lập, lưu bằng chứng làm artifact
backend/                      FastAPI + worker; backend/tests/ (pytest: unit + API)
web/                          React; src/**/*.test.tsx (Vitest), e2e/*.spec.ts (Playwright)
eval/                         Đánh giá với Claude thật (lớp Q) và đo thời gian xử lý (lớp P)
scripts/                      run-tests.sh (chạy + gom bằng chứng), build_test_docs.py (sinh docs từ kết quả)
docs/
  requirements/ design/ plan/ implements/   BRD, PRD, user story, SAD, thiết kế, kế hoạch triển khai
  test-plan.md test-cases.md traceability.md bugs/
  test/                       nguồn: AC đã chốt, test-cases.yaml, kế hoạch IEEE 829 tổng thể
  prompts/ checklists/        prompt và checklist IEEE dùng để soạn tài liệu
reports/<lượt>/               bằng chứng từng lượt chạy
playwright-report/<lượt>/     báo cáo HTML Playwright từng lượt
```

Chạy lại toàn bộ và sinh lại tài liệu truy vết (hồ sơ FAKE, xem mục Kiểm thử bên dưới để dựng stack):

```bash
bash scripts/run-tests.sh run-1
docker compose run --rm --no-deps -v "$PWD:/repo" -w /repo api python scripts/build_test_docs.py
```

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
