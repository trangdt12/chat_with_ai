# T-03 · Đăng nhập giả lập, phiên, phân quyền

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-012 (AC-1, AC-2), US-013 (AC-1, AC-2), US-014 (AC-1, AC-2) | T-02 | 1,5 ngày |

## 1. Mục tiêu
Người dùng chọn một tài khoản mẫu để đăng nhập (thay cho Microsoft 365). Mọi API sau đó biết ai đang gọi, có vai trò gì trong bộ tài liệu nào, và chặn đúng theo bảng quyền ở README §2.4.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/auth/service.py` | Tạo, đọc, hủy phiên |
| `backend/app/auth/policy.py` | `Role`, `AccessContext`, các hàm `can_*` |
| `backend/app/auth/deps.py` | Dependency FastAPI: `current_ctx`, `require_member`, `require_manager`, `require_admin` |
| `backend/app/auth/router.py` | 4 endpoint `/auth/dev-users`, `/auth/login`, `/auth/logout`, `/me` |
| `backend/app/audit.py` | `record_audit(...)` (chữ ký ở README §2.1) |

### 2.2 Chi tiết
**Phiên:**
- Đăng nhập: sinh token `secrets.token_urlsafe(32)`, lưu `sessions(id_hash=sha256(token))`, đặt cookie `cwd_session` (`HttpOnly`, `SameSite=Lax`, `Path=/`). Không lưu token bản rõ.
- Mỗi request: tìm phiên theo hash; nếu không có hoặc `now - last_seen_at > session_idle_hours` → 401 `UNAUTHENTICATED`. Nếu còn hạn thì cập nhật `last_seen_at`.
- Đăng xuất: xóa dòng `sessions`, xóa cookie.

```python
# auth/policy.py
Role = Literal["member", "manager"]

@dataclass(frozen=True)
class AccessContext:
    user_id: UUID
    is_admin: bool
    memberships: dict[UUID, Role]       # doc_set_id → role, đọc từ DB ở MỖI request
    session_id_hash: str

def can_use_content(ctx, dsid) -> bool:   return dsid in ctx.memberships            # xem nội dung, hỏi, tải 1 file
def can_batch_upload(ctx, dsid) -> bool:  return ctx.memberships.get(dsid) == "manager"
def can_view_metadata(ctx, dsid) -> bool: return dsid in ctx.memberships or ctx.is_admin
def can_admin(ctx) -> bool:               return ctx.is_admin
```
- Admin **không** thuộc nhóm thì không có `can_use_content` (BRU-007). Nếu một người vừa là admin vừa là member thì có cả hai loại quyền.
- `require_member(dsid)` → 403 `FORBIDDEN` nếu không có `can_use_content`. Tương tự cho `require_manager`, `require_admin`.
- Thông báo 403 không chứa tên bộ tài liệu hay tên file (AC-US013-1).

**API:**
| Endpoint | Request | Response |
|---|---|---|
| `GET /auth/dev-users` | — | `[{email, display_name}]` mọi user (chỉ dùng cho màn đăng nhập giả lập) |
| `POST /auth/login` | `{email}` | 204 + cookie; email không tồn tại → 404 `USER_NOT_FOUND`. Ghi audit `login` |
| `POST /auth/logout` | — | 204 |
| `GET /me` | — | `{user_id, email, display_name, is_admin, doc_sets: [{id, name, role}]}` |

## 3. Tiêu chí hoàn thành
- [ ] (AC-US012-1) Cho trước chưa đăng nhập; khi gọi bất kỳ API nào ngoài `/auth/*` và `/health`; thì nhận 401 `UNAUTHENTICATED`, không có dữ liệu tài liệu.
- [ ] (AC-US012-2) Cho trước `last_seen_at` cũ hơn 8 giờ; khi gọi API; thì 401 (phía FE giữ câu hỏi đang gõ, làm ở T-04).
- [ ] (AC-US013-1, AC-US014-1) Cho trước `tuan@demo.local` không thuộc nhóm; khi gọi `require_member` cho "Dự án X"; thì 403 `FORBIDDEN`.
- [ ] (AC-US013-2) Cho trước `hung@demo.local` là admin; thì `can_view_metadata` đúng, `can_use_content` sai.
- [ ] (AC-US014-2) Cho trước Lan đang đăng nhập; khi xóa membership của Lan trong DB; thì request kế tiếp của Lan nhận 403 (không cache quyền).

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `tests/auth/test_policy.py` (bảng sự thật) | 4 tài khoản seed × 4 hàm `can_*` đúng bảng README §2.4 |
| `tests/auth/test_session.py::test_login_sets_cookie_and_me` | Login Lan → `/me` có "Dự án X", role `member` |
| `tests/auth/test_session.py::test_idle_expired_401` | Sửa `last_seen_at` lùi 9 giờ → 401 |
| `tests/auth/test_session.py::test_logout_invalidates` | Logout xong dùng lại cookie → 401 |
| `tests/auth/test_policy.py::test_revoke_effective_next_request` | Như AC cuối |
| `tests/auth/test_session.py::test_login_audited` | Có 1 dòng `audit_log(action='login')` |

## 5. Ghi chú
- Không làm CSRF token: cookie `SameSite=Lax` và API chỉ nhận JSON/multipart từ cùng origin là đủ cho bản chạy local.
- Fixture `login_as(email)` trong `tests/conftest.py` để các task sau dùng lại.
- Khi làm: email đăng nhập được chuẩn hóa `strip().lower()`. Ngoài `require_*` có thêm `ensure_member(ctx, dsid)` dùng trong service khi `dsid` chỉ biết sau khi đọc DB (file, trích dẫn, hội thoại). Engine tạo với `hide_parameters=True` để log lỗi SQL không kèm nội dung.
