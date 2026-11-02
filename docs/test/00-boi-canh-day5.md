# Bối cảnh kiểm thử — đọc lại code Day 5

> Ghi lại những gì **đang có trong code** (commit `20031fe`), làm đầu vào cho [test plan](02-test-plan.md). Không phải đặc tả: chỗ nào lệch tài liệu yêu cầu thì ghi rõ.

## 1. Luồng chính (đường xương sống)

```
Đăng nhập dev ─► Xác nhận phân loại ─► POST /doc-sets/{dsid}/documents ─► documents.status = uploaded
                (1 lần / phiên, ghi audit          (kiểm tra magic bytes, ≤ 20 MiB,
                 classification_confirm)            ≤ 50 file/bộ; đổi tên khi trùng)
      │
      ▼  worker (poll 2 s, FOR UPDATE SKIP LOCKED)
 uploaded ─► processing (progress 0→10→95) ─► ready (progress 100)      hoặc ─► failed (corrupt | encrypted | too_many_pages | no_text)
            pypdf đọc từng trang · chia đoạn THEO TRANG (1 chunk = 1 trang) · embedding bge-m3 (hoặc giả)
      │
      ▼
POST /doc-sets/{dsid}/conversations ─► POST /conversations/{cid}/messages  (SSE)
      kiểm tra: chủ hội thoại, thành viên, 1..2000 ký tự, ≥ 1 tài liệu ready (nếu không: 409 NO_READY_DOCUMENTS)
      tìm kiếm kết hợp vector + FTS (RRF) ─► không tìm thấy nếu max_cos < τ và FTS = 0 → KHÔNG gọi Claude
      Claude (search_result + citations) ─► CitationFilter (ALG-05): bỏ khối không nguồn, giữ câu nối
      sự kiện: answer.started → answer.delta* → answer.completed{answer_type, citations[], pending_documents[]}
                                             | answer.stopped | answer.failed{code}
      │
      ▼
GET /citations/{id} ─► {document_id, filename, page, snippet ≤ 300}   (410 DOCUMENT_REMOVED nếu đã gỡ)
GET /documents/{id}/file ─► PDF inline; FE mở `…/file?page=N#page=N`
```

Điểm quan trọng cho kiểm thử:
- `snippet` của trích dẫn = `cited_text` Claude trả về, cắt ở 300 ký tự; `page` = trang của chunk. Vì **1 chunk = 1 trang**, có thể kiểm tra máy "đoạn trích có nằm trên trang đã nêu không" bằng cách đọc lại PDF.
- `pending_documents` = các tài liệu ở trạng thái `uploaded` **hoặc** `processing` tại thời điểm hỏi.
- UI hiện `uploaded` là **"Đã tải lên"**, `processing` là **"Đang xử lý n%"**. Với embedding giả, file 3 trang có thể đi thẳng tới "Sẵn sàng" trước khi FE poll (3 s) kịp thấy "Đang xử lý".
- Không có cột `ready_at`: muốn đo thời gian xử lý phải đo từ phía client (poll API) hoặc đọc log worker.

## 2. Lệnh chạy

| Việc | Lệnh |
|---|---|
| Dựng môi trường | `cp .env.example .env` → `docker compose up -d` → `docker compose exec api alembic upgrade head` → `docker compose exec api python -m app.seed --reset` |
| Chế độ không tốn tiền | `.env`: `LLM_FAKE=1`, `EMBED_FAKE=1`, `RETRIEVAL_NOT_FOUND_TAU=0.25` → `docker compose up -d --force-recreate api worker` |
| Lint + test backend | `docker compose exec api ruff check .` · `docker compose exec api pytest` (DB `cwd_test`, LLM/embedding giả) |
| Unit test frontend | `docker compose exec web npm test` (Vitest) |
| E2E | `cd web && npm install && npx playwright install chromium && npm run e2e` (chạy trên host, mỗi spec tự `seed --reset`) |
| Eval Claude thật | `cd web && npm run eval:corpus` → `docker compose exec api python /eval/run_eval.py --dry-run` → bỏ `--dry-run` (báo cáo ở `eval/reports/YYYY-MM-DD.md`) |
| Smoke Claude | `docker compose exec api python -m app.qa.llm_smoke` |

Nếu pytest báo `database "cwd_test" does not exist`: `docker compose exec db psql -U cwd -d cwd -c "CREATE DATABASE cwd_test OWNER cwd"`.

## 3. URL

| Thành phần | URL |
|---|---|
| Web (Vite dev) | http://localhost:5173 (proxy `/api` → `api:8000`) |
| API | http://localhost:8000/api/v1 · OpenAPI: `docs/design/openapi.json` |
| PostgreSQL | `localhost:5432`, user/pass/db `cwd`/`cwd`/`cwd`; DB test `cwd_test` |

## 4. Tài khoản thử nghiệm (`app/seed.py`, đăng nhập dev — bấm tên trên trang đăng nhập)

| Email | Tên | Vai trò trong "Dự án X" | Dùng cho |
|---|---|---|---|
| `lan@demo.local` | Nguyễn Thị Lan | Thành viên | Người hỏi chính, tải từng file |
| `minh@demo.local` | Trần Văn Minh | Quản lý bộ tài liệu | Tải lô; tài khoản mặc định của `run_eval.py` |
| `hung@demo.local` | Phạm Văn Hùng | Quản trị viên, không thuộc nhóm | Kiểm tra bị chặn nội dung |
| `tuan@demo.local` | Lê Minh Tuấn | — | Người ngoài nhóm |
| `anh@demo.local` | Phạm Đức Anh | Thành viên | Kịch bản gỡ thành viên |

## 5. Dữ liệu PDF mẫu

| Bộ | Nguồn | Nội dung | Dùng ở |
|---|---|---|---|
| Fixture e2e | `web/e2e/fixtures/pdf.ts` (sinh trong bộ nhớ, chữ Latin không dấu) | `HopDongKhung.pdf` 3 trang (30 ngày ở tr.2, ngoại lệ tr.3) · `PhuLuc2.pdf` 1 trang (45 ngày) · `BaoGia_v3.pdf` 1 trang (450 triệu) · `BaoCao.docx` (magic `PK`) · `BangGia_cu.pdf` hỏng · `scan_bienban.pdf` 5 trang trắng | Playwright |
| Fixture pytest | `backend/tests/pdf_factory.py` | PDF sinh bằng code | pytest |
| Corpus eval | `eval/corpus_src.json` → `npm run eval:corpus` → `eval/corpus/*.pdf` (tiếng Việt có dấu, in bằng Chromium) | HopDongKhung, PhuLuc2, BaoGia_v3, KeHoachTrienKhai, DieuKhoanBaoMat, ServiceLevelAgreement | `run_eval.py`, demo |
| Bộ câu hỏi | `eval/questions.yaml` | 20 câu: 8 SC-01, 4 SC-02, 4 SC-03, 4 SC-04, mỗi câu có `expected` và `sources{file,page}` | `run_eval.py` |

**Chưa có:** PDF 50 trang và 200 trang (cần cho NFR-003), PDF đúng 20 MiB. Test plan thêm chúng vào phần dữ liệu cần sinh.
