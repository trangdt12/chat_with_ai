# BUG-003 — FakeLlmClient ghép câu trước vào mọi câu tiếp theo, kể cả câu độc lập

| Trường | Giá trị |
|---|---|
| TC: | — (regression ngoài phạm vi chu kỳ 1: `chat.spec.ts › câu hỏi tiếp nối, câu không có trong tài liệu, Hội thoại mới` — US-010, US-011) |
| Mức nghiêm trọng | S3 — làm đỏ regression ở hồ sơ FAKE; không ảnh hưởng hồ sơ REAL |
| Loại | **Lỗi test double** (`FakeLlmClient` trong `backend/app/qa/llm.py`), không phải lỗi sản phẩm |
| Trạng thái | Đóng |
| Phát hiện ở lượt | run-2 và run-3, commit `2dac54d`, 2026-11-02. Trước đó test này bị skip, vì nằm sau test lỗi của BUG-001 trong file serial |
| Lặp lại | 3/3 lần lặp ở cả 2 lượt |

## Bước tái hiện

1. Hồ sơ FAKE, Lan hỏi lần lượt trong **cùng một hội thoại**:
   - "Thời hạn thanh toán là bao lâu?"
   - "Điều khoản đó có ngoại lệ khi chậm giao hàng không?"
   - "Thủ đô của Pháp là gì?"
2. `cd web && npx playwright test -c e2e/playwright.config.ts chat.spec.ts -g "câu hỏi tiếp nối"`

## Mong đợi

Câu thứ 3 nhận được "Không tìm thấy thông tin này trong các tài liệu đã tải lên."

## Thực tế

```
Expected substring: "Không tìm thấy thông tin này trong các tài liệu đã tải lên."
Received string:    "AITheo tài liệu HopDongKhung.pdf, Ngoai le: khi cham giao hang, … trang 3 …"
```

## Bằng chứng

- [`playwright-report/run-2/index.html`](../../playwright-report/run-2/index.html), [`playwright-report/run-3/index.html`](../../playwright-report/run-3/index.html), test "câu hỏi tiếp nối …"
- [`reports/run-2/playwright.log`](../../reports/run-2/playwright.log)

## Nguyên nhân

Từ lượt thứ 2 của hội thoại, service gọi `rewrite_question` để tạo câu tìm kiếm. `FakeLlmClient.rewrite_question` luôn trả về `"<câu trước> <câu hiện tại>"`. Vì vậy câu tìm kiếm thành "Điều khoản đó có ngoại lệ khi chậm giao hàng không? Thủ đô của Pháp là gì?", nhánh tìm theo từ khóa khớp với hợp đồng, và kết quả không còn là `not_found`.

Claude thật (theo `REWRITE_SYSTEM_PROMPT`) chỉ đưa ngữ cảnh vào khi câu hỏi tham chiếu lượt trước. Bản giả đã không mô phỏng điều đó.

## Cách sửa và xác nhận

- `FakeLlmClient.rewrite_question` chỉ ghép câu trước khi câu hỏi có từ chỉ trỏ (`đó|này|ấy|trên|vậy`). Các pytest về câu tiếp nối (`test_ask_followup_uses_rewrite`, câu có "đó") không đổi và vẫn pass (`pytest tests/qa`: 62 passed).
- Commit sửa: `5ec5abd`. Xác nhận: run-4, run-5 — test PASS 3/3 mỗi lượt, toàn bộ Playwright 66/66 (xem [traceability.md](../traceability.md) §1).
- Việc còn lại: chất lượng viết lại câu hỏi của Claude thật được đo ở lớp Q (TC-051, chu kỳ 2–3).
