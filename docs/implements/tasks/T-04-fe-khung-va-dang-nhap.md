# T-04 · FE: khung ứng dụng, đăng nhập, trang không có quyền

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-012 (AC-1, AC-2), US-013 (AC-1), US-014 (AC-2) | T-01, T-03 | 1,5 ngày |

## 1. Mục tiêu
Có khung SPA với định tuyến, lớp gọi API, màn đăng nhập giả lập và màn "không có quyền". Sau task này, các task FE khác chỉ việc thêm component vào trang có sẵn.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `web/src/api/client.ts` | `apiFetch<T>(path, init)`: thêm `/api/v1`, `credentials: 'include'`, parse lỗi `{code,message}` thành `ApiError`; 401 → gọi `onUnauthenticated()` |
| `web/src/api/types.ts` | Kiểu `Me`, `DocSetRef`, `ApiError` (viết tay theo README §2.3) |
| `web/src/main.tsx`, `web/src/App.tsx` | `QueryClientProvider`, router: `/login`, `/` (ChatPage), `/admin` (AdminPage), `/no-access` |
| `web/src/auth/useMe.ts` | `useQuery(['me'])` gọi `GET /me` |
| `web/src/auth/RequireAuth.tsx` | Chưa có `me` → chuyển `/login`; `doc_sets` rỗng và không phải admin → `/no-access`; admin không thuộc nhóm vào `/` → chuyển `/admin` |
| `web/src/pages/LoginPage.tsx` | Màn 01, bản giả lập |
| `web/src/pages/NoAccessPage.tsx` | Màn 11 |
| `web/src/components/AppHeader.tsx` | Logo "CW · Chat với tài liệu", tên bộ tài liệu, avatar + tên người dùng, nút Đăng xuất, link "Quản trị" nếu `is_admin` |
| `web/src/pages/ChatPage.tsx`, `AdminPage.tsx` | Trang khung rỗng có `AppHeader` (T-07, T-11, T-13, T-14 điền nội dung) |

### 2.2 Chi tiết
**Màn đăng nhập** ([01-dang-nhap.html](../../design/UI_UX_design/01-dang-nhap.html)): giữ bố cục và text tiêu đề "Chat với tài liệu — Hỏi đáp có dẫn nguồn trên tài liệu dự án". Thay nút "Đăng nhập bằng Microsoft 365" bằng danh sách tài khoản từ `GET /auth/dev-users`; bấm một tài khoản → `POST /auth/login` → về trang trước đó (hoặc `/`). Ghi rõ nhãn "Đăng nhập thử nghiệm".
- `?expired=1` → banner "Phiên đăng nhập đã hết hạn. Câu hỏi bạn đang gõ đã được giữ lại và sẽ hiện lại sau khi đăng nhập."

**Giữ câu hỏi khi hết phiên (AC-US012-2):**
```ts
// khi apiFetch nhận 401 lúc đang ở trang chat:
sessionStorage.setItem('cwd.draft', currentDraft)   // ô nhập đăng ký getter qua draftStore
navigate(`/login?expired=1&next=${encodeURIComponent(location.pathname)}`)
// ChatPage (T-11) khi mount: đọc 'cwd.draft' → đổ vào ô nhập → xóa key
```
Ở task này chỉ cần `draftStore` (biến module đơn giản: `setDraftGetter(fn)`, `saveDraft()`, `takeDraft()`).

**Màn không có quyền** ([11-khong-co-quyen.html](../../design/UI_UX_design/11-khong-co-quyen.html)):
- Mặc định (`/me.doc_sets` rỗng): "Bạn chưa có quyền truy cập bộ tài liệu nào", 3 bước hướng dẫn, nút "Sao chép email của tôi", "Tải lại".
- `?revoked=1` (khi API trả 403 lúc đang dùng): "Quyền truy cập của bạn đã thay đổi".
- Không hiển thị tên bộ tài liệu hay tên file.

## 3. Tiêu chí hoàn thành
- [ ] (AC-US012-1) Cho trước chưa đăng nhập; khi mở `/` hoặc `/admin`; thì chuyển tới `/login`.
- [ ] Cho trước ở màn đăng nhập; khi chọn "Nguyễn Thị Lan"; thì vào `/`, header hiện tên Lan và "Dự án X".
- [ ] (AC-US012-2) Cho trước đã gõ câu hỏi; khi API trả 401; thì chuyển `/login?expired=1` có banner, đăng nhập lại thì câu hỏi hiện lại trong ô nhập (kiểm tra đầy đủ sau T-11).
- [ ] (AC-US013-1) Cho trước đăng nhập `tuan@demo.local`; thì thấy màn không có quyền, không có tên bộ tài liệu.
- [ ] (AC-US014-2) Cho trước Lan đang ở `/` và bị gỡ khỏi nhóm; khi thao tác kế tiếp nhận 403; thì chuyển `/no-access?revoked=1`.
- [ ] Đăng xuất → về `/login`; bấm Back không vào lại được trang chat.

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `client.test.ts`: 401 gọi `onUnauthenticated`, lỗi JSON → `ApiError(code)` | Đúng code |
| `RequireAuth.test.tsx`: 3 nhánh (chưa đăng nhập / không nhóm / admin) | Điều hướng đúng |
| `draftStore.test.ts`: `saveDraft` rồi `takeDraft` | Trả nội dung, lần 2 rỗng |

Dùng Vitest + Testing Library; mock `fetch`.

## 5. Ghi chú
- Màu sắc, font, khoảng cách theo `web/src/styles/tokens.css` (T-01). Tham khảo bố cục chung ở [index.html](../../design/UI_UX_design/index.html).
