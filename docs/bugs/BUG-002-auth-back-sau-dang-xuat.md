# BUG-002 — E2E: test đăng xuất giả định Back quay về /login, thực tế ra about:blank

| Trường | Giá trị |
|---|---|
| TC: | — (regression ngoài phạm vi chu kỳ 1: `auth.spec.ts › Lan đăng nhập → thấy bộ tài liệu; đăng xuất thì Back không vào lại được`) |
| Yêu cầu liên quan | Đăng nhập / đăng xuất (ngoài US-001, US-009) |
| Mức nghiêm trọng | S3 — làm đỏ regression, nằm ngoài AC trong phạm vi |
| Loại | **Lỗi test** (không phải lỗi sản phẩm) |
| Trạng thái | Đóng — sau khi sửa, 2 lượt chạy mới đều PASS |
| Phát hiện ở lượt | run-1, commit `cb86f05`, 2026-11-02 |
| Lặp lại | 3/3 lần lặp |

## Bước tái hiện

1. `cd web && npx playwright test -c e2e/playwright.config.ts auth.spec.ts -g "đăng xuất" --repeat-each=3`

## Mong đợi (theo test cũ)

- Sau khi đăng xuất và bấm Back, URL khớp `/\/login/`.

## Thực tế

```
Error: expect(page).toHaveURL(expected) failed
Expected pattern: /\/login/
Received string:  "about:blank"
```

## Bằng chứng

- [`playwright-report/run-1/index.html`](../../playwright-report/run-1/index.html), test "Lan đăng nhập …"
- [`reports/run-1/playwright.log`](../../reports/run-1/playwright.log), mục lỗi 2)–4)

## Nguyên nhân

`LoginPage` (web/src/pages/LoginPage.tsx:30) và nút Đăng xuất (web/src/components/AppHeader.tsx:26) đều gọi `navigate(..., { replace: true })`. Lịch sử của tab vì vậy chỉ còn `[about:blank, /login]`, nên Back ra `about:blank`.

Yêu cầu thật là **"Back không vào lại được"**, và app đáp ứng yêu cầu này: không hiện lại trang đã đăng nhập. Test đã kiểm một chi tiết phụ (URL sau Back), mà chi tiết đó phụ thuộc vào cách app ghi lịch sử.

## Cách sửa và xác nhận

- Đổi assert sau `goBack()` thành: URL **không** phải trang chủ của app, và không có `.topbar` (thanh của người đã đăng nhập).
- Xác nhận: 2 lượt chạy sau khi sửa, PASS 3/3 mỗi lượt.
