# Test plan — "Chat với tài liệu": tải PDF → câu trả lời có trích dẫn

| Mã | Phiên bản | Ngày | Code được kiểm | Liên quan |
|---|---|---|---|---|
| TP-CWD-001-C1 | 1.0 | 2026-11-02 | nhánh `main`, commit ghi trong từng lượt chạy ([traceability.md](traceability.md) §1) | [test-cases.md](test-cases.md) · [traceability.md](traceability.md) · [bugs/](bugs/) · kế hoạch tổng thể IEEE 829: [test/TEST_PLAN.md](test/TEST_PLAN.md) |

Tài liệu này là test plan cho **chu kỳ 1** (đường xương sống, 2 user story). Kế hoạch tổng thể cho mọi user story, theo IEEE 829-2008, nằm ở [test/TEST_PLAN.md](test/TEST_PLAN.md).

---

## 1. Mục tiêu

Chứng minh **bằng bằng chứng máy đọc được** rằng:

1. Một Thành viên tải được 1 file PDF và file đó chuyển tới trạng thái "Sẵn sàng" (**US-001**).
2. Câu trả lời của công cụ có trích dẫn trỏ **đúng tài liệu, đúng trang**, và đoạn trích nằm trên đúng trang đó (**US-009**).

Kết quả đầu ra: mỗi AC trong phạm vi có verdict **PASS / FAIL / BLOCKED**, mỗi verdict có link tới bằng chứng (log, junit, trace, ảnh chụp).

## 2. Phạm vi

### 2.1 Trong phạm vi

| User story | AC đã chốt (bản đo được: [test/01-pham-vi-va-ac.md](test/01-pham-vi-va-ac.md)) |
|---|---|
| **US-001** Tải một file PDF lên (P0) | AC-US001-1a tiếp nhận → ready · 1b thời gian xử lý (NFR-003) · 2 trích dẫn đúng file vừa tải · 3 ghi chú file chưa sẵn sàng · 4 xác nhận phân loại |
| **US-009** Trích dẫn tên tài liệu và số trang (P0) | AC-US009-1 có trích dẫn file + trang · 2 popover ≤ 300 ký tự · 3a đoạn trích nằm trên trang · 3b đoạn trích hỗ trợ câu trả lời · 4 bỏ thông tin không nguồn |

Có **10 AC** và **35 test case** (TC-001..035). Mỗi AC có ít nhất 1 TC, và mỗi TC trỏ về ít nhất 1 AC: xem ma trận ở [test-cases.md](test-cases.md) §2. Script `scripts/build_test_docs.py` kiểm tra hai điều kiện này bằng máy.

Vì sao chọn 2 story này: US-001 là đầu vào của mọi tính năng (chưa có tài liệu "Sẵn sàng" thì không hỏi được), còn US-009 là giá trị cốt lõi (người dùng chỉ tin câu trả lời khi đối chiếu được nguồn). Ghép lại, hai story tạo thành một luồng đi qua cả 3 tiến trình `api`, `worker`, `web`.

### 2.2 Ngoài phạm vi

- Chất lượng câu trả lời theo thống kê (US-006, 007, 008, 010, 011).
- Tải lô (US-002), file bị từ chối (US-004), trùng tên (E-09), bộ tài liệu đầy 50 file (E-08).
- Phân quyền và quản trị (US-012..014, 020..022); Dừng / Sao chép / Đánh giá / Mở PDF (US-015, 017, 018, 019).
- Khả năng tiếp cận, độ phủ code, tải đồng thời (NFR-005), bảo mật, trình duyệt khác Chromium.

Test hiện có của các phần trên **vẫn chạy như regression** trong mỗi lượt, nhưng không tính vào verdict của chu kỳ này. Các TC cho chúng (TC-036 trở đi) thuộc chu kỳ 2–3.

## 3. Chiến lược và phân lớp kiểm thử

| Lớp | Công cụ | Hồ sơ | Kiểm cái gì | Số TC |
|---|---|---|---|---|
| **U** Unit | pytest (`CitationFilter`), Vitest (component React) | — | Quy tắc lọc trích dẫn; hiển thị `[n]`, popover, ghi chú; hộp xác nhận | 8 |
| **I** API tích hợp | pytest + httpx + DB `cwd_test`, LLM giả có kịch bản | FAKE | Hợp đồng SSE, `pending_documents`, mã 409, worker → `ready`, đoạn trích nằm trên trang | 14 |
| **E** End-to-end | **Playwright**, Chromium 1440×900, `--repeat-each=3` | FAKE | Người dùng thấy đúng: "Sẵn sàng" không cần tải lại trang, nút "Nguồn n", popover, ghi chú | 7 |
| **Q** Chất lượng | `eval/run_eval.py`, `eval/check_grounding.py`, CSV người chấm | REAL | Trích dẫn đúng với Claude thật; đoạn trích có trên trang; ngữ nghĩa | 4 |
| **P** Hiệu năng | `eval/measure_ingest.py` | REAL | NFR-003: 50 trang ≤ 120 s, 200 trang ≤ 480 s, đạt cả 3/3 lần | 2 |

Tổng 35 TC: 29 TC chạy được ở hồ sơ FAKE (U, I, E) và chạy tự động mỗi lượt; 6 TC cần hồ sơ REAL (Q, P).

**Thực thi tự động:** [`.github/workflows/tests.yml`](../.github/workflows/tests.yml) chạy [`scripts/run-tests.sh`](../scripts/run-tests.sh) trên GitHub Actions ở mỗi lần push hoặc pull request. Script chạy theo thứ tự `ruff` → `pytest` → `vitest` → TC-005 → `playwright`. Mỗi bước được chạy đến hết để có đủ bằng chứng, kể cả khi bước trước lỗi.

**Lặp lại:** cùng một commit được chạy **2 lượt độc lập** (`run-1`, `run-2`), mỗi lượt dựng stack mới. Trong mỗi lượt, mọi test Playwright lặp 3 lần. Một TC chỉ được tính PASS khi PASS ở cả 2 lượt.

**Không** chấp nhận "chạy lại cho xanh". Không có `retries` trong cấu hình Playwright, nên test chập chờn sẽ hiện thành FAIL.

## 4. Môi trường và dữ liệu kiểm thử

| Hồ sơ | Biến `.env` | Dùng cho |
|---|---|---|
| **FAKE** | `LLM_FAKE=1`, `EMBED_FAKE=1`, `RETRIEVAL_NOT_FOUND_TAU=0.25` | U, I, E — miễn phí, kết quả xác định, chạy trong CI |
| **REAL** | `LLM_FAKE=0`, `EMBED_FAKE=0`, `ANTHROPIC_API_KEY`, τ = 0,35, `LLM_MODEL=claude-opus-5-5` | Q, P — chạy tay, ghi τ, model, cấu hình máy vào báo cáo |

- **Hạ tầng:** Docker Compose gồm `db` (PostgreSQL 16 + pgvector), `api` (FastAPI), `worker`, `web` (Vite). Web ở http://localhost:5173, API ở http://localhost:8000/api/v1.
- **CI:** GitHub Actions `ubuntu-24.04`, Node 20, Chromium do Playwright cài.
- **Tài khoản (seed):** `lan@demo.local` (Thành viên, người chạy chính), `minh@demo.local` (Quản lý). Đăng nhập dev bằng nút có tên người dùng.
- **Dữ liệu được sinh trong code, không commit file nhị phân:**
  - PDF fixture Playwright: [web/e2e/fixtures/pdf.ts](../web/e2e/fixtures/pdf.ts)
  - PDF cho pytest: [backend/tests/pdf_factory.py](../backend/tests/pdf_factory.py) (gồm biên 200 trang và đúng 20 971 520 byte)
  - Corpus eval: `npm run eval:corpus`
  - Bộ câu hỏi: [eval/questions.yaml](../eval/questions.yaml)

  Toàn bộ là dữ liệu giả, không có dữ liệu khách hàng.
- **Cô lập:** mỗi spec E2E tự chạy `app.seed --reset`; pytest dùng DB riêng `cwd_test`.

## 5. Tiêu chí PASS/FAIL, tiêu chí vào/ra

**Định nghĩa verdict của TC** (viết trước khi chạy, chi tiết ở [test-cases.md](test-cases.md) §1):

- **PASS:** lệnh chạy có exit code 0 và mọi mệnh đề "PASS khi" đều đúng. Lớp E phải pass 3/3 lần lặp.
- **FAIL:** có ít nhất 1 mệnh đề sai. Mỗi FAIL phải có bug ticket.
- **BLOCKED:** không đánh giá được. **BLOCKED không phải PASS.**

**Verdict AC:** AC là PASS khi mọi TC của AC đó PASS. Chỉ cần 1 TC bị FAIL hoặc BLOCKED thì AC không PASS.

**Tiêu chí vào:**
- Stack khỏe (`/health` trả 200).
- `ruff check` sạch.
- Định nghĩa PASS/FAIL đã được commit trước lượt chạy đầu tiên.

**Tiêu chí ra (tất cả phải đúng):**
1. 100% AC trong phạm vi có ít nhất 1 TC, và không TC nào thiếu AC (máy kiểm).
2. Mọi TC chạy được ở hồ sơ FAKE (U, I, E, TC-005) đều PASS ở **cả 2 lượt CI**, với cùng verdict.
3. Regression: toàn bộ `pytest`, `vitest`, `playwright` đều xanh.
4. Lớp Q, P: PASS trên hồ sơ REAL, hoặc được PO miễn bằng văn bản. Nếu không, các AC liên quan (1b, 2, 9-1, 3a, 3b) ghi **BLOCKED** kèm lý do.
5. Mọi FAIL có bug ticket; không còn lỗi mức S1–S2 đang mở trong phạm vi.

**Tạm dừng / tiếp tục:**
- Tạm dừng khi: stack không lên được, lớp U hoặc I đỏ (khi đó không chạy E), hoặc kết quả mơ hồ do AC mâu thuẫn.
- Tiếp tục khi nguyên nhân đã có ticket và đã được sửa, và lượt chạy mới bắt đầu từ đầu.

## 6. Rủi ro và giảm thiểu

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Test E2E chập chờn: file nhỏ chuyển sang "Sẵn sàng" trước khi giao diện kịp poll | PASS giả hoặc FAIL ngẫu nhiên | AC-1a chỉ yêu cầu "dãy con" của chuỗi trạng thái; lặp 3 lần × 2 lượt; không dùng retries |
| Hồ sơ FAKE không phản ánh Claude thật | AC đạt ở FAKE nhưng sai khi chạy thật | Lớp Q bắt buộc ở REAL (TC-010, 023, 028, 030) và không được thay bằng FAKE |
| Chưa có máy tham chiếu cho NFR-003 (OI-T3) | Không kết luận được AC-US001-1b | Ghi BLOCKED; chờ chốt máy hoặc PO miễn |
| Các spec dùng chung 1 DB | Spec này ảnh hưởng spec khác | `workers: 1`; mỗi spec tự `seed --reset` |
| AC gốc mơ hồ | Người chạy tự diễn giải | Đã viết lại AC thành dạng đo được ([test/01-pham-vi-va-ac.md](test/01-pham-vi-va-ac.md)), chờ PO duyệt |
| Chi phí khi chạy Claude thật | Vượt ngân sách | Chỉ chạy REAL khi đã sẵn sàng; dùng `--dry-run` trước |

## 7. Vai trò và lịch

| Vai trò | Trách nhiệm |
|---|---|
| QA (người nộp bài) | Viết và duy trì test plan, test case, ma trận; review kết quả CI; mở bug ticket |
| Claude Code (agent) | Viết mã test, script chạy, workflow CI; chạy toàn bộ TC; sinh tài liệu truy vết từ kết quả |
| Developer | Sửa lỗi theo bug ticket |
| Product Owner | Duyệt AC đã viết lại (OI-T1, OI-T2); quyết định miễn cho lớp Q/P |
| Người chấm (2 người BD) | Chấm CSV cho TC-030 (AC-US009-3b) |

| Mốc | Ngày | Việc |
|---|---|---|
| M1 | 2026-10-28 | Chốt AC, viết định nghĩa PASS/FAIL cho TC-001..035 |
| M2 | 2026-11-02 | Viết script chạy, CI, tài liệu truy vết; chạy lượt `run-1`, `run-2` |
| M3 | Khi có ngân sách REAL | Chạy lớp Q (TC-010, 023, 028, 030) và lớp P (TC-006, 007) |
| M4 | Sau M3 | Báo cáo tổng kết, đề xuất đóng chu kỳ 1 |

## 8. Sản phẩm bàn giao và quản lý lỗi

| Sản phẩm | Vị trí |
|---|---|
| Test plan | `docs/test-plan.md` (file này) |
| Test case và ma trận AC ↔ TC | [test-cases.md](test-cases.md), sinh từ [test/test-cases.yaml](test/test-cases.yaml) |
| Truy vết US ↔ AC ↔ TC ↔ bằng chứng | [traceability.md](traceability.md) |
| Bằng chứng mỗi lượt | `reports/<lượt>/`: môi trường, exit code, log từng bước, junit pytest/vitest, `results.json` Playwright, log docker · `playwright-report/<lượt>/`: báo cáo HTML có **trace, ảnh chụp, video** của mọi test, kể cả test PASS |
| Bug ticket | [bugs/](bugs/) — mẫu: [bugs/BUG-000-template.md](bugs/BUG-000-template.md) |
| Mã test | `backend/tests/`, `web/src/**/*.test.tsx`, `web/e2e/*.spec.ts`, `eval/` |
| Script và CI | [scripts/run-tests.sh](../scripts/run-tests.sh), [scripts/build_test_docs.py](../scripts/build_test_docs.py), [.github/workflows/tests.yml](../.github/workflows/tests.yml) |

**Quy trình lỗi:**
1. Một TC có verdict FAIL thì tạo file `docs/bugs/BUG-<số>-<tóm-tắt>.md` theo mẫu. Ticket phải ghi TC, AC, lượt chạy, bước tái hiện, kết quả mong đợi và thực tế, link trace, mức nghiêm trọng S1–S4, nguyên nhân.
2. Developer sửa lỗi.
3. Chạy lại cả 2 lượt.
4. Đóng ticket và ghi link tới lượt chạy xác nhận.

`build_test_docs.py` trả lỗi nếu có TC FAIL mà chưa có ticket.
