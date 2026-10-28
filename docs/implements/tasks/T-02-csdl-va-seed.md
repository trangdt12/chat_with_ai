# T-02 · Models, migration, dữ liệu mẫu

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| Nền tảng | T-01 | 1 ngày |

## 1. Mục tiêu
Có toàn bộ bảng ở README §2.2 trong PostgreSQL, kèm chỉ mục vector và full-text, và một lệnh seed tạo bộ tài liệu cùng tài khoản mẫu để đăng nhập thử.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/models.py` | SQLAlchemy 2 (`DeclarativeBase`, `Mapped[...]`) cho 11 bảng ở README §2.2 |
| `backend/alembic.ini`, `backend/alembic/env.py` | Alembic async, đọc `database_url` từ `Settings` |
| `backend/alembic/versions/0001_init.py` | Extension, bảng, chỉ mục, constraint |
| `backend/app/seed.py` | `python -m app.seed`: idempotent |

### 2.2 Chi tiết
**Extension và các điểm cần làm bằng SQL thô trong migration:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;
-- unaccent() không IMMUTABLE nên bọc lại để dùng trong cột sinh tự động
CREATE FUNCTION f_unaccent(text) RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE
  AS $$ SELECT public.unaccent('public.unaccent', $1) $$;

-- chunks.tsv là cột sinh tự động
tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', f_unaccent(content))) STORED

CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX chunks_tsv_gin ON chunks USING gin (tsv);
CREATE INDEX chunks_doc_idx ON chunks (doc_set_id, document_id);
CREATE INDEX documents_list_idx ON documents (doc_set_id, uploaded_at DESC);
CREATE INDEX turns_conv_idx ON turns (conversation_id, turn_index);
CREATE INDEX audit_set_ts_idx ON audit_log (doc_set_id, ts);
```

**Constraint:**
- `memberships.granted_at timestamptz NOT NULL DEFAULT now()` (màn 08, cột "Thêm lúc").
- `memberships.role IN ('member','manager')`; `documents.status IN ('uploaded','processing','ready','failed')`; `turns.answer_type IN ('answered','not_found','clarification')`; `turns.status IN ('completed','stopped','incomplete')`; `feedback.rating IN ('up','down')`; `audit_log.action IN (...)` đúng 10 hành động ở README §2.3.
- `documents`: `UNIQUE (doc_set_id, filename)`; `progress BETWEEN 0 AND 100`.
- FK: `chunks.document_id → documents ON DELETE CASCADE`; `turns.conversation_id → conversations ON DELETE CASCADE`; `citations.turn_id → turns ON DELETE CASCADE`; `citations.document_id`, `citations.chunk_id` **không** đặt FK (giữ lại được khi tài liệu bị gỡ, T-14).
- `turns`: `UNIQUE (conversation_id, turn_index)`.

**Seed (`app/seed.py`):** tạo nếu chưa có (so theo email / tên).

| Email | Tên hiển thị | Vai trò |
|---|---|---|
| `lan@demo.local` | Nguyễn Thị Lan | member của "Dự án X" |
| `minh@demo.local` | Trần Văn Minh | manager của "Dự án X" |
| `hung@demo.local` | Phạm Văn Hùng | `is_admin = true`, không thuộc nhóm |
| `tuan@demo.local` | Lê Minh Tuấn | chưa thuộc nhóm nào (để thử màn không có quyền) |

Bộ tài liệu: `doc_sets(name='Dự án X')`.

## 3. Tiêu chí hoàn thành
- [ ] Cho trước DB trống; khi chạy `alembic upgrade head`; thì có đủ 11 bảng, extension `vector`, `unaccent` và các chỉ mục trên.
- [ ] Cho trước đã migrate; khi chạy `python -m app.seed` hai lần; thì không lỗi và không tạo trùng dữ liệu.
- [ ] Cho trước insert một `chunks` có `content = 'Thời hạn thanh toán'`; khi truy vấn `tsv @@ websearch_to_tsquery('simple', f_unaccent('thoi han'))`; thì tìm thấy dòng đó.
- [ ] `alembic downgrade base` chạy được (để reset DB khi phát triển).

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `tests/test_models.py::test_unique_filename_per_doc_set` | Insert 2 tài liệu cùng tên trong một bộ → `IntegrityError` |
| `tests/test_models.py::test_delete_document_cascades_chunks` | Xóa document → chunks của nó biến mất, citations giữ nguyên |
| `tests/test_models.py::test_tsv_unaccent` | Như AC thứ 3 |
| `tests/test_seed.py::test_seed_idempotent` | Chạy 2 lần, số user = 4 |

## 5. Ghi chú
- Tham khảo cấu trúc đầy đủ ở [schema.sql](../../design/schema.sql); bản thử nghiệm bỏ các schema riêng, RLS, partition và các bảng billing/analytics.
- Vector 1024 chiều khớp `bge-m3`. Nếu đổi model embedding thì phải sửa số chiều và tạo lại chỉ mục.
- Khi làm: `audit_log.action` có thêm `view_list` (T-07 cần) nên là 11 giá trị. Seed có thêm `anh@demo.local` (Phạm Đức Anh, member "Dự án X") cho kịch bản gỡ thành viên ở T-13/T-15, nên test kiểm tra số user = `len(SEED_USERS)` = 5. Có thêm `python -m app.seed --reset` (T-15 dùng): TRUNCATE mọi bảng và xóa file đã tải lên.
- Test dựng schema bằng `alembic downgrade base` → `upgrade head` một lần mỗi lượt pytest (fixture `_migrate`), fixture `db` TRUNCATE các bảng trước mỗi test.
