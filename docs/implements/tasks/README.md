# Task triển khai — "Chat với tài liệu" (bản thử nghiệm)

> Bản thử nghiệm chạy **local bằng Docker Compose**, tập trung làm ra sản phẩm dùng được. Thiết kế gốc ([SAD](../../design/SAD.md), [Blueprint](../../design/Blueprint_SDD.md)) dùng để tham khảo logic nghiệp vụ và thuật toán; phần hạ tầng AWS, Entra ID và vận hành **không làm** ở bản này (xem §4).
> User story và tiêu chí chấp nhận: [UserStories.md](../../requirements/UserStories.md). Màn hình: [UI_UX_design](../../design/UI_UX_design/index.html).

## 1. Stack và cách chạy

| Thành phần | Lựa chọn | Ghi chú |
|---|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2 (async) + asyncpg, Alembic, pydantic-settings | Một codebase, hai tiến trình: `api` và `worker` |
| CSDL | PostgreSQL 16 + `pgvector` + `unaccent` (image `pgvector/pgvector:pg16`) | Vừa là CSDL chính, vừa là kho vector, vừa là hàng đợi job |
| Đọc PDF | `pypdf` | |
| Embedding | `BAAI/bge-m3` chạy local qua `sentence-transformers` (1024 chiều, đa ngôn ngữ) | Model tải về volume `models/` lần đầu. Đổi sang API khác chỉ cần thay `embeddings.py` |
| AI trả lời | Claude qua **Anthropic API** (`anthropic` Python SDK), model mặc định `claude-opus-5-5` | Cần `ANTHROPIC_API_KEY`. Dùng search-result blocks + citations |
| Lưu file | Ổ đĩa local, volume `data/files/{doc_set_id}/{document_id}.pdf` | |
| Frontend | React 18 + TypeScript + Vite, TanStack Query, `react-markdown` (tắt HTML thô) | Dev server Vite proxy `/api` sang backend |
| Đăng nhập | **Đăng nhập giả lập**: chọn một tài khoản mẫu, không mật khẩu | Thay cho Microsoft 365 |

```bash
cp .env.example .env          # điền ANTHROPIC_API_KEY
docker compose up             # db, api (:8000), worker, web (:5173)
docker compose exec api alembic upgrade head && docker compose exec api python -m app.seed
```

## 2. Quy ước chung (mọi task dùng đúng các tên này)

### 2.1 Cấu trúc thư mục

```
backend/app/
├── main.py            # FastAPI app, gắn router, xử lý lỗi
├── config.py          # Settings (pydantic-settings), mọi ngưỡng ở đây
├── db.py              # engine, session, get_db()
├── models.py          # SQLAlchemy models (toàn bộ bảng)
├── errors.py          # AppError(code, status, message)
├── audit.py           # record_audit(db, user_id, action, doc_set_id, document_id=None, meta=None)
├── seed.py            # tạo bộ tài liệu mẫu + tài khoản mẫu
├── auth/              # router.py, service.py, deps.py (current_user, require_*), policy.py
├── documents/         # router.py, service.py, schemas.py, storage.py
├── ingestion/         # worker.py, pdf.py, chunker.py, embeddings.py
├── qa/                # router.py, service.py, retriever.py, llm.py, citation_filter.py, prompts.py, schemas.py
└── admin/             # router.py, service.py, schemas.py
backend/tests/          # pytest; conftest dựng Postgres thật (docker) + fake LLM, fake embedding
web/src/
├── api/               # client.ts (fetch + xử lý lỗi), sse.ts, types.ts
├── pages/             # LoginPage, ChatPage, AdminPage, NoAccessPage
├── components/        # DocumentSidebar, UploadDialog, ClassificationDialog, ChatThread, AnswerCard, CitationPopover, ...
└── styles/            # design token lấy từ docs/design/UI_UX_design/assets
```

### 2.2 Bảng dữ liệu (`models.py`, một schema `public`)

| Bảng | Cột chính |
|---|---|
| `users` | `id`, `email` (unique), `display_name`, `is_admin` |
| `doc_sets` | `id`, `name` |
| `memberships` | `doc_set_id`, `user_id` (PK kép), `role` (`member` \| `manager`), `granted_at` |
| `sessions` | `id_hash` (PK, SHA-256 của token), `user_id`, `created_at`, `last_seen_at`, `classification_confirmed_at` (nullable) |
| `documents` | `id`, `doc_set_id`, `filename`, `pages`, `size_bytes`, `status` (`uploaded`\|`processing`\|`ready`\|`failed`), `progress` (0–100), `error_code`, `file_path`, `uploaded_by`, `uploaded_at`; unique(`doc_set_id`, `filename`) |
| `chunks` | `id`, `document_id` (FK, `ON DELETE CASCADE`), `doc_set_id`, `page_number`, `chunk_index`, `content`, `tsv` (**cột sinh tự động** `to_tsvector('simple', f_unaccent(content))` — không tự tính khi insert), `embedding` vector(1024); chỉ mục HNSW + GIN |
| `conversations` | `id`, `user_id`, `doc_set_id`, `created_at` |
| `turns` | `id`, `conversation_id`, `turn_index`, `question`, `answer`, `answer_type` (`answered`\|`not_found`\|`clarification`), `status` (`completed`\|`stopped`\|`incomplete`), `created_at` |
| `citations` | `id`, `turn_id`, `idx`, `document_id` (nullable, **không** FK cascade tới `documents` để giữ trích dẫn đã gỡ), `chunk_id` (nullable), `filename` (nullable), `page`, `snippet` (≤ 300, nullable), `removed` (bool) |
| `feedback` | `turn_id`, `user_id` (PK kép), `rating` (`up`\|`down`), `reason` |
| `audit_log` | `id`, `ts`, `user_id`, `action`, `doc_set_id`, `document_id`, `meta` (jsonb, **không chứa nội dung**) |

Id là UUID (trừ `audit_log.id` bigint), thời gian `timestamptz` UTC.

### 2.3 API (`/api/v1`, JSON; lỗi trả `{"code": "...", "message": "..."}`)

| Method & đường dẫn | Ai gọi được | Task |
|---|---|---|
| `GET /auth/dev-users`, `POST /auth/login {email}`, `POST /auth/logout`, `GET /me` | Ai cũng gọi được / đã đăng nhập | T-03 |
| `POST /doc-sets/{dsid}/classification-confirmations` | member, manager | T-05 |
| `POST /doc-sets/{dsid}/documents` (multipart `files[]`; > 1 file chỉ manager) | member, manager | T-05 |
| `GET /doc-sets/{dsid}/documents` | member, manager | T-07 |
| `GET /documents/{id}/file` | member, manager | T-07 |
| `POST /doc-sets/{dsid}/conversations` | member, manager | T-10 |
| `POST /conversations/{cid}/messages` → **SSE** | chủ hội thoại | T-10 |
| `POST /messages/{mid}/stop` | chủ hội thoại | T-10 |
| `GET /citations/{id}` | member, manager | T-10 |
| `PUT /messages/{mid}/feedback` | chủ hội thoại | T-12 |
| `GET /admin/doc-sets`, `GET/POST/PATCH/DELETE /admin/doc-sets/{dsid}/members[/{uid}]` | admin | T-13 |
| `GET /admin/doc-sets/{dsid}/documents`, `DELETE /admin/documents/{id}` | admin | T-14 |
| `GET /admin/audit-logs?doc_set_id&from&to&user_id&action` | admin | T-14 |

**Mã lỗi:** `UNAUTHENTICATED` (401) · `FORBIDDEN` (403) · `NOT_FOUND` (404) · `VALIDATION_ERROR` (422) · `CLASSIFICATION_REQUIRED` (409) · `DOC_SET_FULL` (409) · `NO_READY_DOCUMENTS` (409) · `ALREADY_MEMBER` (409) · `NOT_PDF` (415) · `FILE_TOO_LARGE` (413) · `DOCUMENT_REMOVED` (410) · `USER_NOT_FOUND` (404; dùng cho đăng nhập giả lập và thêm thành viên) · `INTERNAL` (500). Kiểm tra sống: `GET /api/v1/health`.
**Lỗi xử lý tài liệu** (`documents.error_code`): `encrypted`, `corrupt`, `no_text`, `too_many_pages`.
**Hành động audit:** `login`, `classification_confirm`, `upload`, `query`, `view_citation`, `view_file`, `member_add`, `member_remove`, `role_change`, `remove_document`.

### 2.4 Phân quyền (`auth/policy.py`)

| Quyền | member | manager | admin (không thuộc nhóm) |
|---|---|---|---|
| Xem danh sách, trích dẫn, file gốc; hỏi đáp; tải 1 file | ✔ | ✔ | ✘ |
| Tải nhiều file một lần | ✘ | ✔ | ✘ |
| Xem thông tin mô tả tài liệu (tên, trang, dung lượng, trạng thái) | ✔ | ✔ | ✔ |
| Quản lý thành viên, gỡ tài liệu, xem nhật ký | ✘ | ✘ | ✔ |

Quyền được đọc từ DB ở **mỗi request**, nên gỡ thành viên có hiệu lực ngay ở request kế tiếp.

### 2.5 Cấu hình (`config.py`, biến môi trường cùng tên viết hoa)

`database_url`, `files_dir`, `anthropic_api_key`, `llm_model` = `claude-opus-5-5`, `llm_max_tokens` = 4000, `embed_model` = `BAAI/bge-m3`, `upload_max_bytes` = 20 MB, `upload_max_pages` = 200, `doc_set_max_documents` = 50, `chunk_max_chars` = 1800, `chunk_block_max_chars` = 300, `retrieval_top_k_branch` = 30, `retrieval_top_k` = 10, `retrieval_max_per_doc` = 4, `retrieval_not_found_tau` = 0.35, `history_turns` = 6, `question_max_chars` = 2000, `session_idle_hours` = 8, `worker_poll_seconds` = 2, `llm_fake` = false, `embed_fake` = false (bật cho pytest và e2e: trả kết quả giả, không gọi model thật).

### 2.6 Quy ước trích dẫn trong SSE

Backend **không** chèn chuỗi `[n]` vào text. Mỗi `answer.delta` mang `citations` của đoạn text đó; frontend tự hiển thị chỉ số `[n]` sau đoạn text từ danh sách này.

### 2.7 Hai quy tắc giữ nguyên từ thiết kế gốc

1. **Không log nội dung:** log và `audit_log.meta` không chứa câu hỏi, câu trả lời, đoạn văn.
2. **Câu trả lời chỉ dựa trên tài liệu, mọi thông tin có trích dẫn:** chỉ gửi cho Claude các đoạn văn tìm được; câu không có nguồn bị loại (`CitationFilter`).

## 3. Danh sách task

| ID | Task | Story | Phụ thuộc | Ước lượng [GĐ] |
|---|---|---|---|---|
| [T-01](T-01-khoi-tao-du-an.md) | Khởi tạo dự án, Docker Compose, cấu hình | Nền tảng | — | 1 ngày |
| [T-02](T-02-csdl-va-seed.md) | Models, migration, dữ liệu mẫu | Nền tảng | T-01 | 1 ngày |
| [T-03](T-03-dang-nhap-va-phan-quyen.md) | Đăng nhập giả lập, phiên, phân quyền | US-012, US-013, US-014 | T-02 | 1,5 ngày |
| [T-04](T-04-fe-khung-va-dang-nhap.md) | FE: khung ứng dụng, đăng nhập, trang không có quyền | US-012, US-013 | T-01, T-03 | 1,5 ngày |
| [T-05](T-05-api-tai-len.md) | API tải lên (1 file và lô) + xác nhận phân loại | US-001, US-002, US-004 | T-03 | 1,5 ngày |
| [T-06](T-06-worker-xu-ly-tai-lieu.md) | Worker xử lý tài liệu: PDF → đoạn văn → embedding | US-001, US-004, US-005 | T-05 | 2,5 ngày |
| [T-07](T-07-danh-sach-va-fe-tai-lieu.md) | API danh sách + FE thanh tài liệu và tải lên | US-001..005 | T-04, T-05 | 2 ngày |
| [T-08](T-08-tim-kiem-ket-hop.md) | Tìm kiếm kết hợp vector + từ khóa | US-007, US-008, US-010 | T-06 | 1,5 ngày |
| [T-09](T-09-claude-va-citation-filter.md) | Gọi Claude có trích dẫn + CitationFilter | US-007..010 | T-01 | 2,5 ngày |
| [T-10](T-10-api-hoi-dap.md) | API hỏi đáp streaming, câu hỏi tiếp nối, dừng, trích dẫn | US-001, US-006..011, US-016, US-017 | T-08, T-09 | 2,5 ngày |
| [T-11](T-11-fe-hoi-dap.md) | FE hỏi đáp: streaming, trích dẫn, các trạng thái, sao chép, mở PDF | US-006..010, US-016..019 | T-07, T-10 | 3 ngày |
| [T-12](T-12-danh-gia-cau-tra-loi.md) | Đánh giá 👍/👎 (API + FE) | US-015 | T-11 | 0,5 ngày |
| [T-13](T-13-quan-tri-thanh-vien.md) | Quản trị nhóm truy cập và vai trò (API + FE) | US-021 | T-04 | 1,5 ngày |
| [T-14](T-14-go-tai-lieu-va-nhat-ky.md) | Gỡ tài liệu + xem nhật ký truy cập (API + FE) | US-020, US-022 | T-07, T-13 | 2 ngày |
| [T-15](T-15-kiem-thu-va-demo.md) | Kiểm thử end-to-end, bộ câu hỏi đánh giá nhỏ, kịch bản demo | Mọi story | Tất cả | 2 ngày |

**Tổng ≈ 26 ngày công**: 2 developer làm song song khoảng 3 tuần. Đường găng: T-01 → T-02 → T-03 → T-05 → T-06 → T-08 → T-10 → T-11.

## 4. Không làm ở bản thử nghiệm

AWS (Terraform, S3, SQS, Bedrock, KMS), đăng nhập Microsoft 365, CI/CD và môi trường staging/prod, Metabase và sự kiện analytics, giới hạn 30 câu/giờ và trần ngân sách, job dọn dữ liệu định kỳ, xuất CSV nhật ký, canary, cảnh báo, diễn tập khôi phục, kiểm thử hiệu năng và bảo mật chuyên sâu. Khi đi tiếp lên bản chính thức, các phần này đã có thiết kế trong SAD.
