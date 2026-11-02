# BUG-001 — E2E: locator "Nguồn 1" khớp 2 nút khi câu trả lời có 2 khối cùng trích nguồn 1

| Trường | Giá trị |
|---|---|
| TC: | TC-022, TC-027 (cùng test `chat.spec.ts › hỏi → stream → [1] → popover → mở PDF đúng trang`) |
| AC | AC-US009-1, AC-US009-2 |
| Ảnh hưởng thêm (regression) | `admin.spec.ts › gỡ tài liệu …` FAIL 1/3; 6 test còn lại của `chat.spec.ts` bị **skip** (file chạy chế độ serial, test đầu lỗi) |
| Mức nghiêm trọng | S2 — chặn việc xác minh 2 AC trong phạm vi |
| Loại | **Lỗi test** (không phải lỗi sản phẩm) |
| Trạng thái | Đóng — sau khi sửa, 2 lượt chạy mới đều PASS (xem [traceability.md](../traceability.md)) |
| Phát hiện ở lượt | run-1, commit `cb86f05`, 2026-11-02 |
| Lặp lại | chat.spec 3/3 lần lặp; admin.spec 1/3 (phụ thuộc thời điểm stream) |

## Bước tái hiện

1. Stack chạy hồ sơ FAKE (`LLM_FAKE=1`, `EMBED_FAKE=1`, `RETRIEVAL_NOT_FOUND_TAU=0.25`).
2. `cd web && npx playwright test -c e2e/playwright.config.ts chat.spec.ts -g "hỏi → stream" --repeat-each=3`

## Mong đợi (mệnh đề "PASS khi" của TC-022)

- `lastAnswer có button tên khớp /^Nguồn 1: HopDongKhung\.pdf trang \d+$/` (tức là **≥ 1** nút)

## Thực tế

```
Error: locator.getAttribute: Error: strict mode violation:
locator('article.msg-assistant').last().getByRole('button', { name: /^Nguồn 1: HopDongKhung\.pdf trang \d+$/ }) resolved to 2 elements:
  1) <button class="cite" … aria-label="Nguồn 1: HopDongKhung.pdf trang 2">1</button>
  2) <button class="cite" … aria-label="Nguồn 1: HopDongKhung.pdf trang 2">1</button>
    at web/e2e/chat.spec.ts:26
```

Cây a11y lúc lỗi cho thấy câu trả lời **đúng**: 2 câu, mỗi câu có nút `[1]` → HopDongKhung.pdf trang 2; danh sách Nguồn có 1 dòng "HopDongKhung.pdf · trang 2".

## Bằng chứng

- Báo cáo HTML (trace, ảnh, video): [`playwright-report/run-1/index.html`](../../playwright-report/run-1/index.html), test "hỏi → stream …", cả 3 lần lặp
- Log: [`reports/run-1/playwright.log`](../../reports/run-1/playwright.log), mục lỗi 1) và 5)–7)
- Kết quả máy đọc: [`reports/run-1/playwright/results.json`](../../reports/run-1/playwright/results.json)

## Nguyên nhân

`FakeLlmClient` (backend/app/qa/llm.py) trả **2 khối** văn bản, cả hai đều trích search result đầu tiên. Đây là chủ ý, để kiểm việc hiển thị nhiều khối. Giao diện gắn `[1]` sau mỗi khối có nguồn. Đây là hành vi đúng: AC chỉ yêu cầu "≥ 1 nút".

Locator trong test thiếu `.first()`, nên chế độ strict của Playwright báo lỗi khi gặp 2 phần tử. `admin.spec` chỉ lỗi 1/3 vì assert `toBeVisible()` đôi khi chạy lúc khối thứ hai chưa stream xong. Test này chưa từng chạy E2E trước lượt run-1, nên lỗi chưa bị phát hiện.

Không phải lỗi sản phẩm. Không sửa mệnh đề `expect` nào trong test-cases.yaml.

## Cách sửa và xác nhận

- Thêm `.first()` vào 3 locator: `chat.spec.ts` (2 chỗ) và `admin.spec.ts` (1 chỗ).
- Xác nhận: 2 lượt chạy sau khi sửa, cùng commit, PASS 3/3 lần lặp mỗi lượt (xem [traceability.md](../traceability.md) §1).
