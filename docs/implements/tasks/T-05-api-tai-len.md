# T-05 · API tải lên (1 file và lô) + xác nhận phân loại

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-001 (AC-1, AC-4), US-002 (AC-1, AC-2, AC-4), US-004 (AC-1) | T-03 | 1,5 ngày |

## 1. Mục tiêu
Người dùng tải một hoặc nhiều PDF lên bộ tài liệu. Server kiểm tra từng file, lưu xuống đĩa, tạo bản ghi `documents(status='uploaded')` để worker (T-06) xử lý, và trả kết quả riêng cho từng file.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/documents/storage.py` | `save_upload`, `delete_file`, `file_path_for` |
| `backend/app/documents/service.py` | `confirm_classification`, `upload_documents` |
| `backend/app/documents/schemas.py` | `UploadResult` |
| `backend/app/documents/router.py` | 2 endpoint dưới đây |

### 2.2 Chi tiết
**Xác nhận phân loại (AC-US001-4):** `POST /doc-sets/{dsid}/classification-confirmations` (`require_member`) → set `sessions.classification_confirmed_at = now()` cho phiên hiện tại, ghi audit `classification_confirm`, trả 201 `{confirmed_at}`.

**Tải lên:** `POST /doc-sets/{dsid}/documents`, multipart `files[]`.
```python
async def upload_documents(db, ctx, dsid: UUID, files: list[UploadFile]) -> list[UploadResult]

class UploadResult(BaseModel):
    filename: str                       # tên sau khi đổi (nếu trùng)
    id: UUID | None = None
    status: Literal["uploaded"] | None = None
    error_code: str | None = None       # NOT_PDF | FILE_TOO_LARGE | DOC_SET_FULL
```

**Thứ tự kiểm tra:**
| # | Điều kiện | Kết quả |
|---|---|---|
| 1 | Không có `can_use_content` | 403 `FORBIDDEN` (cả request) |
| 2 | `len(files) > 1` và không có `can_batch_upload` | 403 `FORBIDDEN`, message "Chỉ Quản lý bộ tài liệu được tải nhiều file một lần. Vui lòng tải từng file." (AC-US002-4) |
| 3 | `len(files) > doc_set_max_documents` | 422 `VALIDATION_ERROR` |
| 4 | Phiên chưa có `classification_confirmed_at` | 409 `CLASSIFICATION_REQUIRED` (cả request) |
| 5 | Từng file: 5 byte đầu khác `%PDF-` | Kết quả file đó `error_code='NOT_PDF'` |
| 6 | Từng file: kích thước > `upload_max_bytes` | `FILE_TOO_LARGE` (đọc theo khối 1 MB, dừng ngay khi vượt) |
| 7 | Từng file: bộ đã có ≥ `doc_set_max_documents` tài liệu | `DOC_SET_FULL` |
| 8 | Hợp lệ | Lưu file, insert `documents`, kết quả `status='uploaded'` |

- Lỗi từng file không làm hỏng các file khác (AC-US002-2). Response luôn 200 với mảng `UploadResult` theo thứ tự gửi lên.
- **Đếm số tài liệu an toàn khi nhiều người tải cùng lúc:** trong transaction, `SELECT ... FROM doc_sets WHERE id=:dsid FOR UPDATE` rồi mới đếm `documents` và insert.
- **Trùng tên (E-09):** nếu `filename` đã có trong bộ thì đổi thành `Ten (2).pdf`, `Ten (3).pdf`, …
- **Lưu file:** ghi vào `{files_dir}/{dsid}/{document_id}.pdf` (file tạm rồi `os.replace`). Lưu `size_bytes`, `file_path`, `uploaded_by`. `pages` để NULL (worker điền).
- Mỗi file thành công ghi audit `upload` với `document_id`, `meta={"size_bytes": n}` (không ghi tên file vào meta).
- Không cần gửi job: worker tự lấy tài liệu `status='uploaded'` (T-06).

## 3. Tiêu chí hoàn thành
- [ ] (AC-US001-4) Cho trước phiên chưa xác nhận phân loại; khi tải lên; thì 409 `CLASSIFICATION_REQUIRED`. Sau khi xác nhận thì tải được, và có audit `classification_confirm`.
- [ ] (AC-US001-1) Cho trước Lan đã xác nhận; khi tải 1 PDF hợp lệ 5 MB; thì nhận `status='uploaded'`, file có trên đĩa, có dòng `documents`.
- [ ] (AC-US004-1) Cho trước Minh tải 1 file `.docx` (đổi đuôi thành `.pdf` cũng vậy) và 1 PDF hợp lệ; thì file đầu `NOT_PDF`, file sau `uploaded`.
- [ ] (AC-US002-1, 2) Cho trước Minh tải 50 file, có 1 file 25 MB; thì 49 file `uploaded`, 1 file `FILE_TOO_LARGE`.
- [ ] (AC-US002-4) Cho trước Lan là member; khi tải 2 file một lần; thì 403 và không file nào được lưu.
- [ ] Cho trước bộ có 49 tài liệu; khi 2 request tải 1 file chạy đồng thời; thì đúng 1 thành công, 1 `DOC_SET_FULL`.

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `tests/documents/test_upload.py::test_requires_classification` | 409 |
| `…::test_single_pdf_ok` | 200, `uploaded`, file tồn tại |
| `…::test_not_pdf_magic_bytes` | `NOT_PDF` |
| `…::test_too_large` | `FILE_TOO_LARGE`, không để lại file tạm |
| `…::test_member_cannot_batch` | 403 |
| `…::test_duplicate_name_renamed` | Lần 2 tên `a (2).pdf` |
| `…::test_concurrent_last_slot` | Như AC cuối (`asyncio.gather` 2 request) |
| `…::test_admin_not_member_forbidden` | Hùng → 403 |

PDF mẫu nhỏ để test đặt ở `backend/tests/fixtures/pdf/` (dùng chung với T-06).

## 5. Ghi chú
- Giới hạn kiểm tra phía client (đuôi file, 20 MB, số file) làm ở T-07 chỉ để phản hồi nhanh; server luôn kiểm tra lại.
- Kiểm tra số trang và PDF mã hóa/hỏng/scan do worker làm (T-06), vì cần mở file.
