# BUG-004 — E2E "Sao chép kèm nguồn": clipboard Windows trả `\r\n`, regex chỉ khớp `\n`

| Trường | Giá trị |
|---|---|
| TC: | — (regression ngoài phạm vi: `chat.spec.ts › Sao chép kèm nguồn` — US-017) |
| Mức nghiêm trọng | S4 — chỉ xảy ra khi chạy E2E trên máy Windows |
| Loại | **Lỗi test phụ thuộc môi trường** |
| Trạng thái | Đóng |
| Phát hiện | 2026-11-02, khi chạy riêng `chat.spec.ts` để xác nhận bản sửa BUG-003 (máy Windows 10). Trước đó test bị skip, vì nằm sau test lỗi trong file serial |

## Thực tế

```
Expected pattern: /Nguồn:\n\[1\] HopDongKhung\.pdf, trang \d+/
Received string:  "Theo tài liệu HopDongKhung.pdf, … [1]\r\n\r\nNguồn:\r\n[1] HopDongKhung.pdf, trang 2"
```

## Nguyên nhân

`web/src/components/copy.ts` tạo văn bản dùng `\n`; unit test `copy.test.ts` pass. Khi ghi vào clipboard, Windows tự đổi xuống dòng thành `\r\n`, và `navigator.clipboard.readText()` trả về đúng bản đã đổi đó. Trên Linux (CI) không có hiện tượng này. Đây không phải lỗi sản phẩm: dán vào ứng dụng Windows thì `\r\n` mới là đúng.

## Cách sửa và xác nhận

- Trong test, chuẩn hóa `\r\n` thành `\n` trước khi so khớp; regex giữ nguyên.
- Xác nhận: `chat.spec.ts` 7/7 pass, và 2 lượt chạy đầy đủ sau khi sửa (xem [traceability.md](../traceability.md)).
