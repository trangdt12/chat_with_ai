# T-14 · Gỡ tài liệu và xem nhật ký truy cập (API + FE)

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-020 (AC-US020-1, 2), US-022 (AC-US022-1, 2), US-013 (AC-US013-2) | T-07, T-13 | 2 ngày |

## 1. Mục tiêu
Hùng xem danh sách tài liệu chỉ ở dạng thông tin mô tả và gỡ hoàn toàn một tài liệu: file gốc, đoạn văn, embedding và đoạn trích trong lịch sử hội thoại đều bị xóa. Hùng tra cứu nhật ký truy cập theo bộ tài liệu, khoảng thời gian, người dùng và thao tác. Ở bản thử nghiệm không có xuất CSV, không có trạng thái "chờ xóa file".

Màn tham chiếu: [09 Gỡ tài liệu](../../design/UI_UX_design/09-quan-tri-go-tai-lieu.html) (danh sách, xác nhận, đã gỡ), [10 Nhật ký](../../design/UI_UX_design/10-quan-tri-nhat-ky.html) (kết quả, không có kết quả). Bỏ nút "Xuất CSV" và cảnh báo 12 tháng.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/admin/router.py` | `GET /admin/doc-sets/{dsid}/documents`, `DELETE /admin/documents/{id}`, `GET /admin/audit-logs` |
| `backend/app/admin/service.py` | `list_admin_documents`, `purge_document`, `query_audit_logs` |
| `backend/app/documents/storage.py` | Dùng `delete(file_path)` có sẵn (T-05); bỏ qua nếu file không tồn tại |
| `web/src/components/admin/DocumentsTab.tsx` | Bảng mô tả + tìm theo tên file + nút Gỡ |
| `web/src/components/admin/PurgeDialog.tsx` | Hộp xác nhận gỡ |
| `web/src/components/admin/AuditTab.tsx` | Bộ lọc + bảng + phân trang |

### 2.2 Chi tiết

**Danh sách cho admin** (chỉ thông tin mô tả, BRU-007):
```
GET /admin/doc-sets/{dsid}/documents?q=<tên file>
→ 200 [{id, filename, pages, size_bytes, status, error_code, uploaded_by_email, uploaded_at}]
```
Không có trường nội dung, không có link mở file. `q` lọc `filename ILIKE '%q%'`.

**Gỡ tài liệu:**
```
DELETE /admin/documents/{id}   body {requested_by: str (1..200), reason: str (1..500)}  → 200 {id, removed: true}
```
```python
async def purge_document(db, admin: User, document_id: UUID, requested_by: str, reason: str) -> None:
    async with db.begin():
        doc = await db.get(Document, document_id, with_for_update=True)   # None → NOT_FOUND
        await db.execute(update(Citation).where(Citation.document_id == doc.id)
                         .values(snippet=None, filename=None, chunk_id=None, removed=True))
        await db.delete(doc)                     # chunks bị xóa theo ON DELETE CASCADE
        await record_audit(db, admin.id, "remove_document", doc.doc_set_id, doc.id,
                           meta={"requested_by": requested_by, "reason": reason, "pages": doc.pages})
    storage.delete(doc.file_path)                # sau commit; lỗi thì log cảnh báo (không có nội dung), không rollback
```
- `citations.document_id` phải **không** có FK `ON DELETE CASCADE` tới `documents` (để giữ dòng citation đã gỡ). Kiểm tra lại với T-02.
- Tài liệu đang `processing`: worker (T-06) phải bỏ qua khi không tìm thấy document lúc ghi chunks. Ghi chú cho T-06.
- Không phải admin → 403 `FORBIDDEN` (AC-US020-2). `requested_by`/`reason` rỗng → 422 `VALIDATION_ERROR`.
- Người dùng thấy tài liệu biến mất ở lần làm mới danh sách kế tiếp (thanh tài liệu của T-07 polling ≤ 5 s). Trích dẫn cũ gọi `GET /citations/{id}` nhận 410 `DOCUMENT_REMOVED` (T-10 đã xử lý `removed = true`).

**Nhật ký:**
```
GET /admin/audit-logs?doc_set_id=&from=YYYY-MM-DD&to=YYYY-MM-DD&user_id=&action=&cursor=&limit=50
→ 200 {items: [{ts, user_email, action, document_id, document_filename, meta}], next_cursor}
```
- `doc_set_id` bắt buộc; `from`/`to` mặc định 7 ngày gần nhất; `to` tính hết ngày.
- Sắp xếp `ts DESC, id DESC`; cursor = `"{ts_iso}|{id}"`.
- `document_filename` lấy bằng LEFT JOIN `documents` (tài liệu đã gỡ → `null`, FE hiện "—").
- Không ghi audit cho chính thao tác tra cứu (danh sách hành động trong README không có `audit_query`).

**FE gỡ tài liệu:**
- Dòng mô tả: "Bạn chỉ thấy thông tin mô tả của tài liệu, không xem được nội dung."
- Bảng: Tên file · Số trang · Dung lượng (MB, 1 chữ số thập phân) · Người tải lên · Thời điểm · Trạng thái · Thao tác ("Gỡ", màu đỏ).
- `PurgeDialog` (`role="alertdialog"`, focus mặc định ở **Hủy**). Nội dung: tiêu đề "Gỡ hoàn toàn tài liệu?"; "Thao tác không hoàn tác được. File gốc, nội dung đã xử lý và các đoạn trích trong lịch sử hội thoại đều bị xóa."; tên file và người tải lên; ô "Người yêu cầu gỡ *", ô "Lý do *"; ô tích "Tôi hiểu tài liệu sẽ bị xóa vĩnh viễn khỏi công cụ." Nút "Gỡ vĩnh viễn" chỉ bật khi đủ 2 ô và đã tích.
- Thành công: dòng biến mất và hiện toast "Đã gỡ {tên file}. Tài liệu đã biến khỏi danh sách của mọi người dùng. Đã ghi nhật ký."

**FE nhật ký:**
- Bộ lọc: Từ ngày, Đến ngày, Người dùng (thành viên của bộ + admin), Thao tác (nhãn tiếng Việt cho 10 hành động trong README), nút "Tra cứu".
- Bảng: Thời điểm (giờ địa phương, `dd/MM/yyyy HH:mm`) · Người dùng · Thao tác (badge có chữ) · Tài liệu · Ghi chú.
- Ghi chú dựng từ `meta`: lý do gỡ, số trang, vai trò. **Không bao giờ hiển thị câu hỏi hay đoạn văn.**
- Không có kết quả: "Không có bản ghi nào khớp bộ lọc. Thử mở rộng khoảng thời gian hoặc chọn 'Tất cả' ở Người dùng và Thao tác."
- Nút "Sau" khi có `next_cursor`.

## 3. Tiêu chí hoàn thành
- [ ] Cho trước X đang "Sẵn sàng"; khi Hùng gỡ X; thì X biến khỏi danh sách của Lan ≤ 10 s, file trên đĩa bị xóa, không còn dòng `chunks` nào của X, và audit có `remove_document` (AC-US020-1).
- [ ] Cho trước X đã gỡ; khi Lan hỏi 5 câu về nội dung chỉ có trong X; thì cả 5 nhận `not_found` (AC-US020-1).
- [ ] Cho trước một trích dẫn cũ tới X; khi Lan bấm; thì popover báo tài liệu đã được gỡ, không còn đoạn trích hay tên file.
- [ ] Cho trước Lan (không phải admin); khi gọi `DELETE /admin/documents/{id}`; thì 403, và giao diện của Lan không có nút gỡ (AC-US020-2).
- [ ] Cho trước Hùng là admin; khi xem danh sách tài liệu; thì chỉ thấy thông tin mô tả, không mở được nội dung (AC-US013-2).
- [ ] Cho trước một kịch bản thao tác đã biết (đăng nhập, tải lên, hỏi, xem trích dẫn); khi Hùng tra cứu đúng khoảng thời gian; thì nhật ký liệt kê đủ và đúng thứ tự các thao tác đó (AC-US022-1).
- [ ] Không bản ghi nhật ký nào chứa câu hỏi, câu trả lời hay đoạn trích (AC-US022-2).

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `test_purge_removes_chunks_file_and_redacts_citations` | 0 chunks; file không còn; citations `removed=true`, `snippet/filename/chunk_id` null |
| `test_purge_then_query_not_found` (fake embedding + fake LLM) | `answer_type = not_found` |
| `test_purge_forbidden_for_non_admin` | 403 |
| `test_purge_file_missing_on_disk_still_ok` | 200, audit vẫn ghi |
| `test_audit_query_filters_and_cursor` | Lọc theo user/action/ngày đúng; trang 2 không trùng trang 1 |
| `test_audit_meta_never_contains_content` | Quét mọi `meta` sau luồng hỏi đáp: không chứa chuỗi câu hỏi |
| Playwright: gỡ tài liệu → tab Lan không còn file | Pass |
- Khi làm: lọc nhật ký theo bộ tài liệu có kèm các dòng `login` (không gắn bộ) của thành viên **hiện tại** của bộ, để thấy "đăng nhập" trong AC-US022-1. Ngày `from`/`to` tính theo giờ Việt Nam (UTC+7). Response có thêm `id`, `user_id` để FE làm khóa dòng và hiển thị người dùng đích.
