# T-07 · API danh sách tài liệu + FE thanh tài liệu và tải lên

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-001 (AC-1, AC-4), US-002 (AC-1, AC-2, AC-4), US-003 (AC-1), US-004 (AC-1), US-005 (AC-1) | T-04, T-05 | 2 ngày |

## 1. Mục tiêu
Người dùng thấy thanh tài liệu bên trái: danh sách file mới nhất trước, mỗi dòng có tên, số trang và trạng thái. File đang xử lý hiện phần trăm và tự cập nhật, không cần tải lại trang. Người dùng kéo thả PDF để tải lên; lần đầu trong phiên phải qua hộp xác nhận phân loại. Mỗi lỗi được báo riêng từng file. Backend thêm 2 endpoint: danh sách tài liệu và mở file gốc.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/documents/router.py` (sửa) | `GET /doc-sets/{dsid}/documents`, `GET /documents/{id}/file` |
| `backend/app/documents/service.py` (sửa) | `list_documents(db, user, dsid)`, `open_file(db, user, document_id)` |
| `backend/app/documents/schemas.py` (sửa) | `DocumentOut` |
| `web/src/api/documents.ts` | `listDocuments`, `uploadFiles` (XHR để có % tải lên), `confirmClassification` |
| `web/src/components/DocumentSidebar.tsx` | Danh sách + vùng kéo thả + nút "Hội thoại mới" ở cuối (nút gắn hành vi ở T-11) |
| `web/src/components/DocumentRow.tsx` | Một dòng: tên, số trang, trạng thái, thanh tiến trình, lý do lỗi |
| `web/src/components/UploadDropzone.tsx` | Kéo thả / chọn file, kiểm tra phía client |
| `web/src/components/ClassificationDialog.tsx` | Màn 03 |
| `web/src/components/BatchResultPanel.tsx` | Kết quả tải lô cho manager (màn 04 `#manager`) |
| `web/src/components/EmptyState.tsx` | Màn 02: chưa có tài liệu, đang xử lý |
| `web/src/hooks/useDocuments.ts` | TanStack Query + polling |

### 2.2 Chi tiết

**`GET /doc-sets/{dsid}/documents`** (member, manager; admin bị 403 vì admin dùng trang quản trị ở T-14):

```json
[{ "id": "uuid", "filename": "HopDongKhung.pdf", "pages": 48, "size_bytes": 1048576,
   "status": "processing", "progress": 62, "error_code": null,
   "uploaded_by": "Nguyễn Thị Lan", "uploaded_at": "2026-11-10T03:00:00Z" }]
```
Sắp xếp `uploaded_at DESC`, trả toàn bộ (tối đa 50 file nên không phân trang). Ghi audit `view_list` tối đa 1 lần/phút cho mỗi người, để polling không làm đầy nhật ký.

**`GET /documents/{id}/file?page=N`** (member, manager của bộ chứa tài liệu): trả `FileResponse(media_type="application/pdf", headers={"Content-Disposition": "inline"})` và ghi audit `view_file`. Tài liệu không còn → 410 `DOCUMENT_REMOVED`. Tham số `page` chỉ để FE ghép `#page=N` vào URL; server bỏ qua.

**Polling trạng thái (thay cho SSE):**

```ts
useQuery({
  queryKey: ["documents", dsid],
  queryFn: () => listDocuments(dsid),
  refetchInterval: (q) =>
    q.state.data?.some(d => d.status === "uploaded" || d.status === "processing") ? 3000 : false,
});
```
Chu kỳ 3 giây đáp ứng yêu cầu "cập nhật ít nhất mỗi 5 giây" (AC-US005-1). Sau mỗi lần tải lên xong thì `invalidateQueries(["documents", dsid])`.

**Luồng tải lên:**
1. Kiểm tra phía client: đuôi `.pdf`, ≤ 20 MB, tổng số file sau khi thêm ≤ 50. Member chọn > 1 file → báo "Tải lô chỉ dành cho Trưởng nhóm. Hãy tải từng file." và không gửi (AC-US002-4). Đây chỉ là phản hồi nhanh; server (T-05) vẫn kiểm tra lại.
2. Gửi `POST /doc-sets/{dsid}/documents`. Nếu nhận 409 `CLASSIFICATION_REQUIRED` → mở `ClassificationDialog`. Bấm "Xác nhận và tải lên" → `POST …/classification-confirmations` → gửi lại đúng các file đó.
3. Trong lúc tải, hiện dòng tạm "Đang tải lên 40%" (từ `xhr.upload.onprogress`). Lỗi mạng: tự thử lại tối đa 3 lần, hiện "Mất kết nối, đang thử lại… (n/3)" (E-10).
4. Server trả 200 kèm mảng `UploadResult` theo thứ tự gửi (T-05): `status="uploaded"` thì file xuất hiện trong danh sách; nếu `filename` khác tên đã gửi thì hiện toast "đã đổi tên"; có `error_code` thì hiện toast riêng kèm lý do.

**`ClassificationDialog`** (màn 03): tiêu đề "Xác nhận phân loại tài liệu"; liệt kê tên các file sắp tải; 4 ô phân loại (Công khai, Nội bộ được tải; Mật, Tuyệt mật không được tải); checkbox xác nhận; nút chính **bị vô hiệu cho tới khi tích**; Esc = Hủy; focus nằm trong hộp thoại.

**Thông báo lỗi** (lấy nguyên văn từ màn 04):

| Mã | Thông báo |
|---|---|
| `NOT_PDF` | Chỉ hỗ trợ file PDF. |
| `FILE_TOO_LARGE`, `too_many_pages` | File vượt quá giới hạn 200 trang / 20 MB. |
| `DOC_SET_FULL` | Bộ tài liệu đã đạt tối đa 50 file. File “{tên}” không được tiếp nhận. |
| Trùng tên (server đã đổi tên) | {tên} đã tồn tại. File mới được lưu thành {tên mới}. |
| `no_text` | Không trích xuất được chữ (có thể là bản scan). Bản MVP chưa hỗ trợ PDF scan. |
| `encrypted` | File được bảo vệ bằng mật khẩu. Hãy gỡ mật khẩu rồi tải lại. |
| `corrupt` | File bị hỏng hoặc không đọc được. Hãy xuất lại PDF và thử lại. |

**Nhãn trạng thái:** `uploaded` = "Đang chờ xử lý", `processing` = "Đang xử lý n%", `ready` = "Sẵn sàng", `failed` = "Lỗi" kèm lý do.

**Trạng thái trống** (màn 02): chưa có tài liệu → hướng dẫn 3 bước; mọi tài liệu đang xử lý → banner "Đang xử lý n tài liệu". `ChatPage` (T-11) đọc `readyCount` từ `useDocuments` để bật/tắt nút Gửi.

**Kết quả tải lô** (manager, màn 04 `#manager`): sau khi gửi lô, hiện bảng tổng hợp Sẵn sàng / Đang xử lý / Lỗi (tự cập nhật theo polling) và danh sách "File cần xử lý" kèm gợi ý hành động.

## 3. Tiêu chí hoàn thành
- [ ] Cho trước bộ có 5 file, khi mở trang, thì thấy đúng 5 dòng, mới nhất ở trên, mỗi dòng có tên, số trang, trạng thái (AC-US003-1).
- [ ] Cho trước một file đang xử lý, khi xem danh sách, thì phần trăm tự tăng mà không tải lại trang, rồi chuyển "Sẵn sàng" hoặc "Lỗi" (AC-US005-1).
- [ ] Cho trước lần tải đầu trong phiên, khi chưa tích xác nhận, thì nút tải lên bị vô hiệu; sau khi xác nhận, file được tải lên (AC-US001-4).
- [ ] Cho trước 1 file `.docx` và 1 PDF hỏng, khi tải lên, thì mỗi file có thông báo riêng đúng lý do và không file nào "Sẵn sàng" (AC-US004-1).
- [ ] Cho trước manager kéo thả 50 PDF, khi tải, thì mỗi file có dòng riêng; file lỗi không chặn các file khác (AC-US002-1, AC-US002-2).
- [ ] Cho trước member chọn nhiều file, thì lô không được gửi và có hướng dẫn tải từng file (AC-US002-4).
- [ ] Người không thuộc nhóm gọi `GET …/documents` hoặc `GET /documents/{id}/file` → 403, không lộ tên file (AC-US013-1).

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `test_list_documents_sorted_desc` (API) | Thứ tự `uploaded_at DESC`, đủ trường |
| `test_list_documents_forbidden_for_outsider_and_admin` | 403 |
| `test_open_file_ok_and_removed` | 200 `application/pdf`; tài liệu đã xóa → 410 |
| `test_open_file_writes_audit` | Có bản ghi `view_file` |
| Vitest `UploadDropzone` | Chặn `.docx`, file > 20 MB, member chọn nhiều file |
| Vitest `ClassificationDialog` | Nút chính bị vô hiệu tới khi tích; Esc đóng hộp thoại |
| Vitest `useDocuments` | Có file `processing` → polling 3 s; hết → dừng |
| Thủ công trên trình duyệt | Kéo thả PDF thật → "Đang xử lý" → "Sẵn sàng" tự cập nhật |

## 5. Ghi chú
- Giao diện bám màn [02](../../design/UI_UX_design/02-trang-thai-trong.html), [03](../../design/UI_UX_design/03-xac-nhan-phan-loai.html), [04](../../design/UI_UX_design/04-tai-tai-lieu-len.html) và design token trong `UI_UX_design/assets`.
- Định dạng response khi tải lô (kết quả từng file, tên mới khi trùng) theo T-05; nếu T-05 đổi thì cập nhật `uploadFiles` cho khớp.
- Khi làm: thêm hành động audit `view_list` vào constraint (T-02). Logic tải lên nằm ở `web/src/hooks/useUpload.tsx` để thanh tài liệu và màn trống dùng chung.
