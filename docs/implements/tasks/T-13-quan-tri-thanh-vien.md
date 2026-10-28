# T-13 · Quản trị nhóm truy cập và vai trò (API + FE)

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-021 (AC-US021-1..5); hỗ trợ AC-US002-4, AC-US014-2 | T-04 | 1,5 ngày |

## 1. Mục tiêu
Hùng (admin) mở `/admin`, chọn bộ tài liệu, xem danh sách thành viên. Hùng thêm thành viên theo email, đổi vai trò Thành viên ↔ Quản lý bộ tài liệu và gỡ thành viên. Gỡ có hiệu lực ngay ở request kế tiếp của người bị gỡ. Trang quản trị không có lối tắt nào tới nội dung tài liệu.

Màn tham chiếu: [08 Nhóm truy cập](../../design/UI_UX_design/08-quan-tri-nhom-truy-cap.html) (danh sách, thêm, không có tài khoản, đã gỡ). Ở bản thử nghiệm, đổi chữ "Microsoft 365 công ty" thành "hệ thống".

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/admin/router.py` | Các route `/admin/doc-sets…`; mọi route `Depends(require_admin)` |
| `backend/app/admin/service.py` | `list_doc_sets`, `list_members`, `add_member`, `change_role`, `remove_member` |
| `backend/app/admin/schemas.py` | `DocSetOut`, `MemberOut`, `AddMemberIn`, `ChangeRoleIn` |
| `web/src/pages/AdminPage.tsx` | Khung quản trị: chọn bộ tài liệu, 3 tab (Nhóm truy cập · Gỡ tài liệu · Nhật ký) |
| `web/src/components/admin/MembersTab.tsx` | Bảng thành viên, đổi vai trò, gỡ |
| `web/src/components/admin/AddMemberDialog.tsx` | Hộp thêm thành viên |

### 2.2 Chi tiết

```
GET    /admin/doc-sets                          → 200 [{id, name, member_count}]
GET    /admin/doc-sets/{dsid}/members           → 200 [{user_id, email, display_name, role, granted_at}]
POST   /admin/doc-sets/{dsid}/members           {email, role: "member"|"manager"} → 201 MemberOut
PATCH  /admin/doc-sets/{dsid}/members/{uid}     {role} → 200 MemberOut
DELETE /admin/doc-sets/{dsid}/members/{uid}     → 204
```
`granted_at` cần thêm cột `memberships.granted_at timestamptz default now()` (đề xuất bổ sung README §2.2). Nếu không thêm cột thì bỏ cột "Thêm lúc" khỏi bảng.

| Điều kiện | Kết quả | Audit |
|---|---|---|
| Không phải admin | 403 `FORBIDDEN` | — |
| `dsid` không tồn tại | 404 `NOT_FOUND` | — |
| Email không có trong `users` (so sánh không phân biệt hoa thường, đã `strip`) | 404 `USER_NOT_FOUND` | — |
| Đã là thành viên | 409 `ALREADY_MEMBER` | — |
| Thêm hợp lệ | 201 | `member_add`, `meta={"target_user_id", "role"}` |
| Đổi vai trò | 200 | `role_change`, `meta={"target_user_id", "from", "to"}` |
| Gỡ | 204 | `member_remove`, `meta={"target_user_id"}` |
| PATCH/DELETE với `uid` không phải thành viên | 404 `NOT_FOUND` | — |

`meta` chỉ chứa id và vai trò, không chứa email.

**Hiệu lực ngay:** không cache quyền. `auth/deps.py` (T-03) đọc `memberships` ở mỗi request, nên không cần làm thêm gì; task này chỉ cần test xác nhận.

**FE:**
- Ô chọn bộ tài liệu lấy từ `GET /admin/doc-sets`; nhớ lựa chọn trong `localStorage` (bọc try/catch).
- Dòng chú thích dưới tiêu đề: "Chỉ thành viên trong nhóm mới xem và hỏi được tài liệu. Gỡ thành viên có hiệu lực ngay ở thao tác kế tiếp của họ."
- Ghi chú BRU-007: "Quản trị viên không có quyền xem hay hỏi nội dung tài liệu. Muốn xem, hãy tự thêm mình vào nhóm như một Thành viên; thao tác này được ghi nhật ký."
- Bảng: Thành viên · Email · Vai trò (`<select>` có nhãn ẩn "Vai trò của {tên}") · Thêm lúc · Thao tác (nút "Gỡ", `aria-label="Gỡ {tên} khỏi nhóm"`). Chân bảng: "{n} thành viên · {m} Quản lý bộ tài liệu".
- Hộp thêm: ô "Email", radio vai trò ("Thành viên — xem, hỏi, tải từng file" / "Quản lý bộ tài liệu — thêm quyền tải lô"), nút Hủy/Thêm. Lỗi `USER_NOT_FOUND` hiện ngay dưới ô email: "Không tìm thấy tài khoản này trong hệ thống. Kiểm tra lại email."; `ALREADY_MEMBER`: "Tài khoản này đã thuộc nhóm."
- Gỡ: hỏi xác nhận, sau đó toast "Đã gỡ {tên} khỏi nhóm. Quyền hết hiệu lực từ thao tác kế tiếp của người này. Đã ghi nhật ký."
- Không có liên kết nào sang `/` hay tới tài liệu từ trang này (AC-US021-5).

## 3. Tiêu chí hoàn thành
- [ ] Cho trước `tuan.lm@congty.vn` có trong `users` và chưa thuộc nhóm; khi Hùng thêm với vai trò Thành viên; thì người này xuất hiện trong bảng, đăng nhập thì xem và hỏi được, và audit có `member_add` (AC-US021-1).
- [ ] Cho trước email không có trong `users`; khi thêm; thì báo lỗi tại ô email và nhóm không đổi (AC-US021-2).
- [ ] Cho trước Phạm Đức Anh là thành viên; khi Hùng gỡ; thì request kế tiếp của Anh tới `GET /doc-sets/{dsid}/documents` trả 403, và audit có `member_remove` (AC-US021-3, AC-US014-2).
- [ ] Cho trước Lan là Thành viên; khi Hùng đổi thành Quản lý; thì Lan tải lô được, và audit có `role_change` (AC-US021-4).
- [ ] Cho trước Hùng là admin; khi mở trang nhóm; thì không có lối tắt nào tới nội dung tài liệu (AC-US021-5).

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `test_admin_routes_forbidden_for_member_and_manager` | 403 cho mọi route `/admin/*` |
| `test_add_member_unknown_email` | 404 `USER_NOT_FOUND`, không có dòng mới |
| `test_add_member_duplicate` | 409 `ALREADY_MEMBER` |
| `test_remove_member_effective_next_request` | Sau DELETE, cùng cookie gọi list documents → 403 |
| `test_role_change_enables_batch_upload` | Sau PATCH manager, upload 2 file → 202 |
| `test_audit_meta_has_no_email` | `meta` chỉ có id, vai trò |
| Playwright: thêm email sai → lỗi tại ô; thêm đúng → dòng mới | Đúng text |
- Khi làm: API thêm/đổi vai trò trả 201/200 như bảng §2.2; test "upload 2 file" kỳ vọng 200 (theo T-05, không phải 202). Xác nhận gỡ thành viên dùng hộp thoại `alertdialog` (`components/Modal.tsx`).
