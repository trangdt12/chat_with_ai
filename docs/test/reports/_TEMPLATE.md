# Báo cáo kiểm thử — <YYYY-MM-DD> (lượt <n>, agent-browser)

<!-- Chép file này thành docs/test/reports/<YYYY-MM-DD>.md. Số liệu lấy từ results.yaml, không gõ tay. -->

| Mục | Giá trị |
|---|---|
| Code | `<commit>` (+ thay đổi chưa commit: có/không) |
| Hồ sơ | FAKE (`LLM_FAKE=1`, `EMBED_FAKE=1`, `RETRIEVAL_NOT_FOUND_TAU=0.25`) |
| URL app | http://localhost:5173 |
| Công cụ | agent-browser `<phiên bản>`, Chrome `<phiên bản>`, viewport 1440×900 |
| Máy | `<OS, CPU, RAM>` |
| Định nghĩa PASS/FAIL | [test-cases.yaml](../test-cases.yaml) — viết trước khi chạy, không sửa `expect` sau khi chạy |
| Kết quả máy đọc được | [results.yaml](results.yaml), vòng `<round id>` |
| Trạng thái lượt | xong / **dừng** — `<stopped_reason>` |

## Kiểm môi trường trước khi chạy

| Kiểm tra | Kết quả |
|---|---|
| `docker compose ps` — db, api, worker, web đều `Up` | |
| `GET /api/v1/health` = 200 | |
| `GET http://localhost:5173` = 200 | |
| `.env` ở hồ sơ FAKE | |
| `data/e2e-fixtures/` đủ 6 file | |

## Verdict từng TC (agent-browser, 3 lượt/TC)

| TC | AC | r1 | r2 | r3 | Verdict | Bằng chứng |
|---|---|---|---|---|---|---|
| TC-004 | AC-US001-1a | | | | | [<ngày>/agent-browser/TC-004/](<ngày>/agent-browser/TC-004/) |
| TC-009 | AC-US001-2 | | | | | |
| TC-014 | AC-US001-3 | | | | | |
| TC-017 | AC-US001-4 | | | | | |
| TC-018 | AC-US001-4 | | | | | |
| TC-022 | AC-US009-1 | | | | | |
| TC-027 | AC-US009-2 | | | | | |

Verdict TC = PASS chỉ khi 3/3 lượt PASS; có lượt FAIL ⇒ FAIL; còn lại ⇒ BLOCKED.

## Chi tiết FAIL / BLOCKED

<!-- Mỗi TC không PASS một mục. Xóa phần này nếu không có. -->

### TC-xxx — lượt r<n> — FAIL | BLOCKED

- **Dòng `expect` sai / không chấm được:** `<chép nguyên văn dòng expect>`
- **Quan sát được:** `<trích snapshot, dòng nào>`
- **Bằng chứng:** `<đường dẫn 02-after.txt, ảnh>`
- **Ticket:** `<link>` (bắt buộc với FAIL, tiêu chí thoát 6)

## Verdict từng AC (AC PASS ⇔ mọi TC của AC đó PASS, gồm cả các lớp U/I/Q/P)

| AC | TC lớp E (lượt này) | TC lớp khác (lấy từ báo cáo trước) | Verdict |
|---|---|---|---|
| AC-US001-1a | TC-004 | TC-001, 002, 003, 005 | |
| AC-US001-2 | TC-009 | TC-008, 010 | |
| AC-US001-3 | TC-014 | TC-011, 012, 013 | |
| AC-US001-4 | TC-017, 018 | TC-015, 016 | |
| AC-US009-1 | TC-022 | TC-019, 020, 021, 023 | |
| AC-US009-2 | TC-027 | TC-024, 025, 026 | |

<!-- AC không có TC lớp E (AC-US001-1b, AC-US009-3a, 3b, 4): chép verdict từ báo cáo trước. Nguồn: test-cases.yaml, trường `ac`. -->

| AC | Verdict |
|---|---|
| AC-US001-1b | |
| AC-US009-3a | |
| AC-US009-3b | |
| AC-US009-4 | |

## So với Playwright

| TC | Playwright (`run` trong test-cases.yaml) | agent-browser | Khớp? |
|---|---|---|---|
| | | | |

## Câu hỏi đã gửi người / chờ quyết định

| # | TC / lượt | Loại (môi trường chết / kết quả mơ hồ / AC mâu thuẫn) | Câu hỏi | Trả lời |
|---|---|---|---|---|
| | | | | |

## Lượt tiếp theo

1.
