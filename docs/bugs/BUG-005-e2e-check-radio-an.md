# BUG-005 — E2E "👎 kèm lý do": `check()` trên radio ẩn bị timeout

| Trường | Giá trị |
|---|---|
| TC: | — (regression ngoài phạm vi: `chat.spec.ts › 👎 kèm lý do` — US-018) |
| Mức nghiêm trọng | S3 — làm đỏ regression |
| Loại | **Lỗi test** |
| Trạng thái | Đóng |
| Phát hiện | 2026-11-02, khi chạy riêng `chat.spec.ts` sau khi sửa BUG-003 và BUG-004. Trước đó test bị skip, vì nằm sau test lỗi trong file serial |

## Thực tế

```
Test timeout of 90000ms exceeded.   (bước answer.getByLabel("Thiếu thông tin").check())
```

Cây a11y lúc lỗi: nhóm "Vì sao câu trả lời chưa tốt?" hiện đủ 4 radio, mặc định chọn "Sai thông tin", nút "Gửi đánh giá" sẵn sàng.

## Nguyên nhân

`web/src/styles/pages.css:33`: `.chip input { position: absolute; opacity: 0; pointer-events: none; }`. Radio được ẩn đi, người dùng bấm vào chip `<label>`. `locator.check()` bấm thẳng vào input; vì input không nhận sự kiện con trỏ, Playwright chờ tới khi hết thời gian.

Với người dùng, bấm chip vẫn chọn đúng radio (label bao input), và bàn phím vẫn dùng được (`:focus-visible` có viền). Unit test `AnswerCard.test.tsx` "👎 mở 4 lý do…" (bấm vào label) pass.

## Cách sửa và xác nhận

- Test bấm vào `label.chip` có chữ "Thiếu thông tin", rồi assert radio `toBeChecked()`. Assert cuối (`aria-pressed="true"`) giữ nguyên.
- Commit sửa: `5ec5abd`. Xác nhận: run-4, run-5 — PASS 3/3 mỗi lượt.
