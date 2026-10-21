# T-06 · Worker xử lý tài liệu: PDF → đoạn văn → embedding

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-001 (AC-US001-1), US-004 (AC-US004-1), US-005 (AC-US005-1) | T-05 | 2,5 ngày |

## 1. Mục tiêu
Tiến trình `worker` lấy các tài liệu `uploaded` mà T-05 đã lưu, đọc PDF, phát hiện lỗi (mật khẩu, hỏng, scan, quá 200 trang), chia đoạn theo trang, tạo embedding bằng bge-m3 rồi lưu vào `chunks`. Khi xong, tài liệu chuyển sang `ready` và tìm kiếm được (T-08). Trong lúc chạy, cột `progress` được cập nhật để FE hiển thị phần trăm.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/ingestion/worker.py` | Vòng lặp lấy job, gọi pipeline, cập nhật trạng thái. Chạy bằng `python -m app.ingestion.worker` |
| `backend/app/ingestion/pdf.py` | `extract_pages(path) -> list[str]`, `is_scanned(pages) -> bool`, lỗi `PdfError(code)` |
| `backend/app/ingestion/chunker.py` | `chunk_pages(pages) -> list[ChunkDraft]`, `split_blocks(text, max_chars) -> list[str]` (T-09 dùng lại) |
| `backend/app/ingestion/embeddings.py` | `class Embedder`: `embed_documents(texts)`, `embed_query(text)` |
| `docker-compose.yml` (sửa) | Service `worker` dùng image backend, `command: python -m app.ingestion.worker`, volume `data/` và `models/` |
| `backend/tests/ingestion/test_chunker.py`, `test_pdf.py`, `test_worker.py` | Xem §4 |

### 2.2 Chi tiết

**Vòng lặp worker** (một tiến trình, xử lý tuần tự từng tài liệu):

```python
async def run_forever() -> None:
    embedder = Embedder(settings.embed_model)          # tải model 1 lần khi khởi động
    while True:
        doc_id = await claim_next_document()
        if doc_id is None:
            await asyncio.sleep(settings.worker_poll_seconds); continue
        await process_document(doc_id, embedder)
```

```sql
-- claim_next_document(): một transaction ngắn, an toàn khi chạy nhiều worker
UPDATE documents SET status = 'processing', progress = 0
WHERE id = (SELECT id FROM documents WHERE status = 'uploaded'
            ORDER BY uploaded_at FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING id;
```

Khi khởi động, worker đưa các tài liệu kẹt ở `processing` (do worker chết giữa chừng) về `uploaded`, để chúng được xử lý lại.

**`process_document(doc_id, embedder)`:**

| Bước | Việc | Lỗi → `status='failed'`, `error_code` |
|---|---|---|
| 1 | Đọc file `documents.file_path` bằng `pypdf.PdfReader` | Không mở được → `corrupt` |
| 2 | `reader.is_encrypted`: thử `reader.decrypt("")`; thất bại → lỗi | `encrypted` |
| 3 | `len(reader.pages) > settings.upload_max_pages` | `too_many_pages` |
| 4 | `pages = [p.extract_text() or "" for p in reader.pages]`; ghi `documents.pages = len(pages)` | Lỗi khi trích xuất → `corrupt` |
| 5 | `is_scanned(pages)` (ALG-01) | `no_text` |
| 6 | `drafts = chunk_pages(pages)`; `progress = 10` | — |
| 7 | Embedding theo lô 32 đoạn; sau mỗi lô `progress = 10 + 85 * done / total` (commit riêng để FE thấy) | Exception bất kỳ → `corrupt` + log `document_id`, loại lỗi |
| 8 | Một transaction: `DELETE FROM chunks WHERE document_id = :id` → insert toàn bộ chunks → `status='ready', progress=100` | — |

Bước 8 xóa trước rồi mới ghi, nên chạy lại cho cùng kết quả.

**Tài liệu bị gỡ trong lúc đang xử lý (T-14):** trước bước 8 và trước mỗi lần cập nhật `progress`, kiểm tra dòng `documents` còn tồn tại. Nếu không còn (hoặc file đã bị xóa khỏi đĩa), dừng xử lý, log `document_id` ở mức info và bỏ qua; **không** đánh dấu `failed`, không ném lỗi.

**ALG-01, phát hiện bản scan:** `sparse = số trang có len(text.strip()) < 30`; nếu `sparse / len(pages) >= 0.8` → bản scan.

**ALG-02, chia đoạn** (`chunker.py`, Python thuần, không I/O):

```python
@dataclass(frozen=True)
class ChunkDraft:
    page_number: int        # 1-based
    chunk_index: int        # tăng liên tục trong cả tài liệu
    content: str            # ≤ chunk_max_chars

def chunk_pages(pages: list[str], max_chars: int = 1800) -> list[ChunkDraft]: ...
def split_sentences(text: str) -> list[str]: ...
def split_blocks(text: str, max_chars: int = 300) -> list[str]: ...
```

- Chuẩn hóa từng trang: `unicodedata.normalize("NFC", text)`, gộp khoảng trắng liên tiếp, bỏ dòng trống thừa. Bỏ qua trang rỗng.
- `split_sentences`: tách sau `.`, `!`, `?`, `…`, `;` khi sau đó là khoảng trắng, và tách ở xuống dòng. **Không** tách bên trong số (`1.000,5`, `3.2`).
- Gom câu tham lam tới `max_chars`; khi đoạn đầy thì đoạn mới bắt đầu bằng câu cuối của đoạn trước (chồng lấn 1 câu). Câu dài hơn `max_chars` thì cắt cứng tại khoảng trắng gần nhất.
- **Không đoạn nào chứa văn bản của 2 trang.**
- `split_blocks`: gom câu của một đoạn thành các khối ≤ 300 ký tự (câu dài hơn thì cắt tại khoảng trắng). Hàm phải tất định: T-09 gọi lại hàm này lúc hỏi đáp để tạo các khối con trong search_result.

**Embedding** (`embeddings.py`):

```python
class Embedder:
    def __init__(self, model_name: str): ...           # SentenceTransformer(model_name), cache ở /models
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...  # normalize_embeddings=True
    def embed_query(self, text: str) -> list[float]: ...
```

- Văn bản đưa vào embedding: `f"{filename} · trang {page}\n{content}"`. Tiền tố này chỉ dùng để tạo embedding, **không** lưu vào `content`.
- bge-m3 cho vector 1024 chiều, khớp cột `embedding vector(1024)`.
- Hàm chạy đồng bộ (CPU), nên worker gọi qua `await asyncio.to_thread(...)`.
- Trong test dùng `FakeEmbedder`: vector tất định sinh từ hash của text.

**Cột `tsv`:** là cột sinh tự động (T-02), nên worker **không** ghi vào cột này khi insert.

## 3. Tiêu chí hoàn thành
- [ ] Cho trước một PDF văn bản 50 trang ở `uploaded`, khi worker chạy, thì tài liệu chuyển `processing` → `ready` trong ≤ 2 phút trên máy dev, `progress` tăng dần, và `chunks` có `page_number` đúng (AC-US001-1, AC-US005-1).
- [ ] Cho trước PDF có mật khẩu / PDF hỏng / PDF scan / PDF 201 trang, khi xử lý, thì `status='failed'` với `error_code` lần lượt `encrypted` / `corrupt` / `no_text` / `too_many_pages`, và không có chunk nào (AC-US004-1).
- [ ] Cho trước worker bị dừng khi đang xử lý, khi khởi động lại, thì tài liệu đó được xử lý lại và không bị trùng chunk.
- [ ] Hai worker chạy song song không xử lý cùng một tài liệu.
- [ ] Log chỉ có `document_id`, số trang, số đoạn, thời gian; không có nội dung.

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `test_chunk_never_crosses_page` | Mọi `ChunkDraft` chỉ chứa văn bản của đúng 1 trang |
| `test_chunk_max_len_and_overlap` | `len(content) ≤ 1800`; đoạn sau bắt đầu bằng câu cuối của đoạn trước |
| `test_long_sentence_hard_split` | Câu 4.000 ký tự → các đoạn ≤ 1800, cắt tại khoảng trắng |
| `test_split_sentences_keeps_numbers` | `"Giá 1.000,5 triệu. Hạn 30 ngày."` → 2 câu |
| `test_split_blocks_deterministic` | Gọi 2 lần cho cùng kết quả; mọi khối ≤ 300 |
| `test_is_scanned` | 10 trang, 8 trang < 30 ký tự → True; 7 trang → False |
| `test_pdf_errors` (fixture PDF trong `tests/fixtures/`) | Đúng 4 mã lỗi |
| `test_worker_happy_path` (Postgres thật + `FakeEmbedder`) | `ready`, `progress=100`, số chunk > 0 |
| `test_worker_rerun_idempotent` | Chạy `process_document` 2 lần → số chunk không đổi |
| `test_claim_skip_locked` | 2 lần claim đồng thời trả 2 id khác nhau |
| `test_worker_document_deleted_midway` | Xóa document khi đang embedding → worker dừng êm, không lỗi, không còn chunk mồ côi |

## 5. Ghi chú
- Tham khảo: Blueprint ALG-01, ALG-02 ([Blueprint_SDD.md §3.8](../../design/Blueprint_SDD.md)).
- Lần chạy đầu, bge-m3 (≈ 2,2 GB) tải về volume `models/`, nên lâu. Nếu máy dev quá chậm, có thể đổi `embed_model` sang một model đa ngôn ngữ 1024 chiều nhẹ hơn; đổi model thì phải xử lý lại toàn bộ tài liệu.
- PDF chỉ có owner password (`decrypt("")` thành công) vẫn được nhận.
