# Chat với tài liệu — hướng dẫn cho agent

Hỏi đáp có dẫn nguồn trên PDF. Docker Compose: `db` (PostgreSQL + pgvector), `api` (FastAPI), `worker`, `web` (React/Vite). Cách chạy app, tài khoản mẫu: [README.md](README.md). Yêu cầu: [docs/requirements](docs/requirements). Thiết kế: [docs/design](docs/design).

## Kiểm thử

Nguồn sự thật, theo thứ tự ưu tiên:

1. AC: [docs/test/01-pham-vi-va-ac.md](docs/test/01-pham-vi-va-ac.md)
2. Định nghĩa PASS/FAIL của từng TC (khối `expect`): [docs/test/test-cases.yaml](docs/test/test-cases.yaml)
3. Test plan (phạm vi, tiêu chí vào/thoát): [docs/test-plan.md](docs/test-plan.md). Ma trận AC↔TC: [docs/test-cases.md](docs/test-cases.md) (sinh từ YAML bằng `scripts/build_test_docs.py`). Kết quả và bằng chứng: [docs/traceability.md](docs/traceability.md)

### Môi trường test

| Thành phần | Giá trị |
|---|---|
| URL app | http://localhost:5173 (Vite, proxy `/api` → `api:8000`) |
| API | http://localhost:8000/api/v1 (kiểm sống: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health`, phải là 200) |
| Hồ sơ | **FAKE** cho lớp E: `.env` có `LLM_FAKE=1`, `EMBED_FAKE=1`, `RETRIEVAL_NOT_FOUND_TAU=0.25` |
| Tài khoản | Đăng nhập dev: bấm nút có tên người dùng. Người chạy chính là **Nguyễn Thị Lan** (`lan@demo.local`) |
| Đặt lại dữ liệu | `docker compose exec -T api python -m app.seed --reset` (xóa DB `cwd` và file đã tải) |
| File để tải lên | `data/e2e-fixtures/` (sinh bằng `cd web && npm run e2e:fixtures`; byte giống hệt fixture Playwright): `HopDongKhung.pdf` (3 trang), `PhuLuc2.pdf`, `BaoGia_v3.pdf`, `BaoCao.docx`, `BangGia_cu.pdf`, `scan_bienban.pdf` |

### Cấu hình Playwright (tham chiếu; agent-browser phải chạy cùng điều kiện)

[web/e2e/playwright.config.ts](web/e2e/playwright.config.ts): `baseURL` = `E2E_BASE_URL` hoặc `http://localhost:5173`, Chromium **1440×900**, `locale: vi-VN`, `workers: 1` (dùng chung DB, chạy tuần tự), timeout 90 s/test, `expect` 15 s. Lệnh: `cd web && npm run e2e`; từng TC lớp E chạy theo trường `run` trong `test-cases.yaml` (`--repeat-each=3`).

agent-browser **không thay** verdict Playwright: kết quả agent-browser ghi riêng (`method: agent-browser`), báo cáo nêu cả hai.

### Lệnh agent-browser

Đã cài toàn cục (`npm i -g agent-browser`, `agent-browser install`). Mọi lệnh đều có `--session <tên>`; mỗi lượt chạy của một TC dùng một session riêng tên `tc-<số>-r<lượt>`, ví dụ `tc-004-r1`.

```sh
S="--session tc-004-r1"
agent-browser $S open http://localhost:5173
agent-browser $S set viewport 1440 900
agent-browser $S snapshot -i -c                                  # cây a11y có ref @eN
agent-browser $S find role button click --name "Nguyễn Thị Lan"  # đăng nhập dev
agent-browser $S upload "#docs-panel [data-testid=file-input]" data/e2e-fixtures/HopDongKhung.pdf
agent-browser $S check @e5                                       # ref lấy từ snapshot gần nhất
agent-browser $S is enabled @e6
agent-browser $S fill @e7 "Thời hạn thanh toán là bao lâu?" && agent-browser $S press Enter
agent-browser $S wait 2000
agent-browser $S get text "#docs-panel"
agent-browser $S get count "[role=dialog]"
agent-browser $S eval "<js>"                                     # có await Promise
agent-browser $S screenshot docs/test/reports/<ngày>/agent-browser/TC-004/r1/after.png
agent-browser $S close                                           # luôn đóng, kể cả khi FAIL
```

Ref `@eN` chỉ đúng cho snapshot vừa lấy. Sau mỗi thao tác làm đổi trang, phải snapshot lại trước khi dùng ref.

Ánh xạ locator Playwright → agent-browser (từ [web/e2e/helpers.ts](web/e2e/helpers.ts)):

| Playwright | agent-browser |
|---|---|
| `chooseFiles` | `upload "#docs-panel [data-testid=file-input]" <file>` |
| `docRow(name)` | `get text "#docs-panel"`, tìm dòng `.doc-row` chứa tên file |
| hộp xác nhận phân loại | dialog "Xác nhận phân loại tài liệu", checkbox, nút "Xác nhận và tải lên" |
| `ask(q)` | ô có nhãn "Câu hỏi về tài liệu" → `fill` → `press Enter` |
| `lastAnswer` | `article.msg-assistant` cuối cùng; nút nguồn có tên `Nguồn n: <file> trang <p>`; `.sources`, `.pending-note` |

### Thư mục báo cáo

Mọi đầu ra của agent đều nằm trong `docs/test/reports/`:

```
docs/test/reports/
├── results.yaml                    # file kết quả máy đọc được: agent CẬP NHẬT file này
├── _TEMPLATE.md                    # mẫu báo cáo lượt chạy
├── <YYYY-MM-DD>.md                 # báo cáo lượt, chép từ _TEMPLATE.md
└── <YYYY-MM-DD>/agent-browser/TC-xxx/r<n>/
    ├── cmds.log                    # mọi lệnh agent-browser đã chạy, theo thứ tự, kèm output
    ├── 01-before.txt               # snapshot sau khi mở, trước thao tác chính
    ├── 02-after.txt                # snapshot sau thao tác
    └── *.png                       # ảnh chụp lúc chấm (bắt buộc khi FAIL)
```

Mẫu báo cáo: [docs/test/reports/_TEMPLATE.md](docs/test/reports/_TEMPLATE.md). Cấu trúc `results.yaml` ghi trong phần đầu file đó.

### Quyền hạn khi chạy test

Khởi động phiên chạy test bằng `claude --settings .claude/settings.test-run.json`. File này cấp quyền và chặn sửa ở mức harness.

**Được làm:**
- Chạy `agent-browser`.
- Ghi và tạo file trong `docs/test/reports/`, cập nhật `docs/test/reports/results.yaml`.
- Chạy các lệnh hạ tầng mà `given`/`when` của TC yêu cầu: `seed --reset`, `docker compose stop|start worker`, `docker compose ps`, `npm run e2e:fixtures`.

**Không được làm:**
- Sửa code: `backend/`, `web/src/`, `web/e2e/`, `web/scripts/`, `eval/`, `docker-compose.yml`, `.env`.
- Sửa AC hay định nghĩa test: `docs/requirements/`, `docs/test/01..03-*.md`, `docs/test/test-cases.yaml`. Không đổi, nới hay "diễn giải lại" một dòng `expect` sau khi đã thấy kết quả.
- Chạy lại một lượt FAIL cho tới khi xanh. Chỉ được chạy lại khi lượt trước BLOCKED vì hạ tầng, và phải ghi rõ lý do.

### Cách thực thi một TC

Phạm vi: các TC có `layer: E` trong `test-cases.yaml` (TC-004, 009, 014, 017, 018, 022, 027). Mỗi TC chạy **3 lượt**, mỗi lượt một session mới. TC chỉ PASS khi 3/3 lượt PASS.

Mỗi lượt:

1. **Chuẩn bị:** thực hiện `given` của TC (thường là `seed --reset`, đăng nhập Lan, tải file và chờ "Sẵn sàng").
2. **Mở:** `open` URL app → `set viewport 1440 900`.
3. **Snapshot** → lưu `01-before.txt`.
4. **Thao tác:** thực hiện đúng bước `when`, không thêm bước.
5. **Snapshot** → lưu `02-after.txt`. Chụp ảnh nếu cần làm bằng chứng.
6. **Chấm:** đối chiếu **từng dòng `expect`** với snapshot hoặc output lệnh. Mỗi dòng ghi `ok: true/false` và trích dẫn bằng chứng (file + dòng). Lượt PASS ⇔ mọi dòng `ok: true`. Một dòng sai ⇒ FAIL. Không đánh giá được ⇒ BLOCKED (BLOCKED không phải PASS).
7. **Đóng** session, ghi kết quả vào `results.yaml`.

Bước đặc thù theo TC (để hiện thực đúng `expect`, không thay `expect`):

| TC | Ghi chú thực thi |
|---|---|
| TC-004 | Trước khi upload: `eval "window.__abMark=1"`. Sau khi thấy "Sẵn sàng": `eval "window.__abMark"` phải ra `1` (chứng minh không tải lại trang). Chờ "Sẵn sàng" tối đa 60 s. |
| TC-009 | Tải `HopDongKhung.pdf` rồi `BaoGia_v3.pdf`, chờ cả hai "Sẵn sàng" rồi mới hỏi. |
| TC-014 | Sau khi `HopDongKhung.pdf` "Sẵn sàng": `docker compose stop worker` → tải `BaoGia_v3.pdf` → thấy "Đã tải lên" → hỏi. **Luôn** chạy `docker compose start worker` khi kết thúc lượt, kể cả lúc FAIL hoặc dừng giữa chừng. |
| TC-017 | TC cần 2 phiên mới. Mỗi lượt dùng 2 session `tc-017-r<n>a` (tải `HopDongKhung.pdf`) và `tc-017-r<n>b` (tải `BangGia_cu.pdf`). Kiểm nút "Xác nhận và tải lên" bằng `is enabled` trước khi `check`. |
| TC-018 | Sau khi chọn `BaoGia_v3.pdf`, chạy ngay `eval "new Promise(r=>{let m=0;const t=setInterval(()=>{m=Math.max(m,document.querySelectorAll('[role=dialog]').length)},100);setTimeout(()=>{clearInterval(t);r(m)},2000)})"`. Kết quả phải là `0`. |
| TC-022, TC-027 | Chuẩn bị: seed, Lan tải `HopDongKhung.pdf`. Hỏi "Thời hạn thanh toán là bao lâu?". Với TC-027: lấy `p` từ tên nút `Nguồn 1: …`, bấm nút đó, snapshot dialog. |

### Dừng và hỏi người

Gặp một trong các trường hợp sau thì **dừng**, ghi `status: stopped` và `stopped_reason` vào `results.yaml`, rồi hỏi người. Không tự diễn giải thay nhóm.

- **Môi trường chết:** URL app hoặc API không trả 200, container không `Up` (`docker compose ps`), `seed --reset` lỗi, agent-browser không khởi chạy được, hoặc app không ở hồ sơ FAKE.
- **Kết quả mơ hồ:** một dòng `expect` không chấm được rõ ràng đúng/sai từ snapshot; UI khác mô tả (đổi nhãn, đổi locator); kết quả giữa các lượt không ổn định mà không rõ nguyên nhân.
- **AC mâu thuẫn:** `expect` mâu thuẫn với AC, với một TC khác, hoặc với hành vi hiển nhiên đúng; `test-cases.yaml` trỏ tới AC không có trong `01-pham-vi-va-ac.md`.

Khi hỏi, nêu: TC, lượt, dòng `expect`, bằng chứng (đường dẫn snapshot/ảnh), và các cách hiểu có thể. Không đề xuất sửa `expect`.
