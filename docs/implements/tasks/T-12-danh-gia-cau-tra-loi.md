# T-12 · Đánh giá câu trả lời 👍/👎 (API + FE)

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-015 (AC-US015-1, AC-US015-2) | T-11 | 0,5 ngày |

## 1. Mục tiêu
Dưới mỗi câu trả lời đã hoàn tất có hai nút 👍/👎. Bấm 👎 thì hiện danh sách lý do. Mỗi người chỉ có một đánh giá cho mỗi câu trả lời; bấm lại nút kia thì đánh giá được thay. Màn tham chiếu: [05 Hỏi đáp, trạng thái "Đánh giá 👎"](../../design/UI_UX_design/05-hoi-dap.html#feedback).

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/qa/router.py` | Thêm `PUT /messages/{mid}/feedback` |
| `backend/app/qa/service.py` | `submit_feedback(db, user, turn_id, rating, reason)` |
| `backend/app/qa/schemas.py` | `FeedbackIn`, `FeedbackOut` |
| `web/src/components/FeedbackButtons.tsx` | Hai nút + danh sách lý do |
| `web/src/components/AnswerCard.tsx` | Gắn `FeedbackButtons` (chỉ khi lượt `completed`) |

### 2.2 Chi tiết

```python
class FeedbackIn(BaseModel):
    rating: Literal["up", "down"]
    reason: Literal["wrong", "missing", "wrong_source", "other"] | None = None

class FeedbackOut(BaseModel):
    turn_id: UUID
    rating: Literal["up", "down"]
    reason: str | None
```

| Điều kiện | Kết quả |
|---|---|
| Chưa đăng nhập | 401 `UNAUTHENTICATED` |
| `mid` không tồn tại | 404 `NOT_FOUND` |
| Người gọi không phải chủ hội thoại của lượt | 403 `FORBIDDEN` |
| Lượt không ở `status = completed` | 422 `VALIDATION_ERROR` |
| `rating = up` mà có `reason` | Bỏ qua `reason` (lưu `NULL`) |
| Hợp lệ | Upsert, trả 200 `FeedbackOut` |

```sql
INSERT INTO feedback (turn_id, user_id, rating, reason) VALUES (:tid, :uid, :rating, :reason)
ON CONFLICT (turn_id, user_id) DO UPDATE SET rating = EXCLUDED.rating, reason = EXCLUDED.reason;
```

**FE:**
- 👍: gửi ngay `{rating: "up"}`; nút được đánh dấu đã chọn (`aria-pressed="true"`).
- 👎: mở danh sách lý do (radio): "Sai thông tin" (`wrong`), "Thiếu thông tin" (`missing`), "Nguồn không đúng" (`wrong_source`), "Lý do khác" (`other`), cùng nút "Gửi đánh giá". Gửi xong thì đóng danh sách và đánh dấu 👎.
- Đánh giá vừa gửi được giữ trong state của lượt; bấm nút còn lại thì gửi đè.
- Lỗi mạng: toast "Không gửi được đánh giá, thử lại", giữ trạng thái cũ.

## 3. Tiêu chí hoàn thành
- [ ] Cho trước câu trả lời đã hoàn tất; khi Lan bấm 👎; thì hiện 4 lý do; sau khi chọn và gửi, đánh giá được lưu và nút 👎 được đánh dấu (AC-US015-1).
- [ ] Cho trước Lan đã đánh giá 👍; khi bấm 👎 và gửi lý do; thì bảng `feedback` chỉ có 1 dòng cho (lượt, Lan) với `rating = down` (AC-US015-2).
- [ ] Cho trước lượt `stopped` hoặc `incomplete`; khi hiển thị; thì không có nút đánh giá.

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `test_feedback_upsert_replaces_previous` | Gửi up rồi down → 1 dòng, `down` |
| `test_feedback_other_user_forbidden` | Người khác chủ hội thoại → 403 |
| `test_feedback_not_completed_turn` | Lượt `stopped` → 422 |
| Playwright: 👎 → chọn "Thiếu thông tin" → Gửi | Nút 👎 `aria-pressed=true` |
