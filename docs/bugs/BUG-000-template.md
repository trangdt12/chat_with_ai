# BUG-000 — <tóm tắt một dòng: cái gì sai, ở đâu>

> Mẫu. Chép thành `BUG-<số 3 chữ số>-<tóm-tắt-không-dấu>.md`. Trường `TC:` dùng mã thật để
> `scripts/build_test_docs.py` nối ticket với TC trong [../traceability.md](../traceability.md). File mẫu này không dùng mã TC thật.

| Trường | Giá trị |
|---|---|
| TC: | TC-xxx |
| AC | AC-USxxx-n |
| Mức nghiêm trọng | S1 chặn · S2 nặng · S3 vừa · S4 nhẹ |
| Trạng thái | Mở · Đang sửa · Chờ xác nhận · Đóng · Không sửa (ghi lý do) |
| Phát hiện ở lượt | run-N, commit `xxxxxxx`, ngày |
| Lặp lại | x/3 lần lặp, ở y/2 lượt |
| Người phát hiện / người sửa | |

## Bước tái hiện

1. `docker compose exec -T api python -m app.seed --reset`
2. …
3. Lệnh chạy TC: `…` (lấy từ cột "Lệnh chạy" trong [../test-cases.md](../test-cases.md))

## Mong đợi (mệnh đề "PASS khi" bị vi phạm)

- `…` (chép nguyên văn từ test-cases.md)

## Thực tế

- …

## Bằng chứng

- Trace: `playwright-report/run-N/data/<id>.zip` (mở bằng `npx playwright show-trace`)
- Ảnh chụp / video: `playwright-report/run-N/index.html` → test → Attachments
- Log: `reports/run-N/<bước>.log`, dòng …

## Nguyên nhân

Sau khi phân tích: lỗi sản phẩm, lỗi test, hay lỗi môi trường. Với lỗi test hoặc lỗi môi trường, ghi rõ vì sao không phải lỗi sản phẩm.

## Cách sửa và xác nhận

- Commit sửa: `xxxxxxx`
- Lượt chạy xác nhận: run-N (PASS 3/3) và run-M (PASS 3/3)
