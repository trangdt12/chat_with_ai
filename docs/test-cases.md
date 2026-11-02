# Test case — US-001 và US-009 (định nghĩa PASS/FAIL)

> **Sinh tự động** bằng `scripts/build_test_docs.py` từ [test/test-cases.yaml](test/test-cases.yaml) (nguồn sự thật). Không sửa tay file này.
> Định nghĩa viết ngày **2026-10-28** cho commit `20031fe`, **trước** lượt chạy đầu tiên (xem lịch sử git của file YAML). File này chỉ chứa định nghĩa; kết quả chạy nằm ở [traceability.md](traceability.md).
> AC đã chốt: [test/01-pham-vi-va-ac.md](test/01-pham-vi-va-ac.md). Test plan: [test-plan.md](test-plan.md).

## 1. Quy tắc verdict (áp dụng cho mọi TC)

| Verdict | Điều kiện |
|---|---|
| **PASS** | Lệnh `run` kết thúc exit code 0, **và** mọi mệnh đề trong "PASS khi" đúng (đã hiện thực thành assert trong mã test). Lớp E: pass **3/3** lần lặp (`--repeat-each=3`). |
| **FAIL** | Bất kỳ mệnh đề nào sai, hoặc ≥ 1 lần lặp lớp E lỗi. Mọi FAIL phải có bug ticket trong [bugs/](bugs/). |
| **BLOCKED** | Không đánh giá được: skip, thiếu hạ tầng (Claude thật, bge-m3), chưa có kết quả. **BLOCKED không phải PASS.** |

Tính lặp lại: mỗi TC phải cho **cùng verdict ở ≥ 2 lượt chạy độc lập** (CI matrix `run-1`, `run-2`).

## 2. Ma trận AC ↔ TC

| User story | AC | Test case | Lớp |
|---|---|---|---|
| US-001 | **AC-US001-1a** | [TC-001](#tc-001) · [TC-002](#tc-002) · [TC-003](#tc-003) · [TC-004](#tc-004) · [TC-005](#tc-005) | I E |
| US-001 | **AC-US001-1b** | [TC-006](#tc-006) · [TC-007](#tc-007) | P |
| US-001 | **AC-US001-2** | [TC-008](#tc-008) · [TC-009](#tc-009) · [TC-010](#tc-010) | I E Q |
| US-001 | **AC-US001-3** | [TC-011](#tc-011) · [TC-012](#tc-012) · [TC-013](#tc-013) · [TC-014](#tc-014) | U I E |
| US-001 | **AC-US001-4** | [TC-015](#tc-015) · [TC-016](#tc-016) · [TC-017](#tc-017) · [TC-018](#tc-018) | U I E |
| US-009 | **AC-US009-1** | [TC-019](#tc-019) · [TC-020](#tc-020) · [TC-021](#tc-021) · [TC-022](#tc-022) · [TC-023](#tc-023) | U I E Q |
| US-009 | **AC-US009-2** | [TC-024](#tc-024) · [TC-025](#tc-025) · [TC-026](#tc-026) · [TC-027](#tc-027) | U I E |
| US-009 | **AC-US009-3a** | [TC-028](#tc-028) · [TC-029](#tc-029) | I Q |
| US-009 | **AC-US009-3b** | [TC-030](#tc-030) | Q |
| US-009 | **AC-US009-4** | [TC-031](#tc-031) · [TC-032](#tc-032) · [TC-033](#tc-033) · [TC-034](#tc-034) · [TC-035](#tc-035) | U I |

**Kiểm tra độ phủ (máy):** 10 AC · 35 TC · AC không có TC: **0** · TC không trỏ về AC: **0**.

Ngoài phạm vi: TC-036 trở đi trong YAML thuộc các user story khác (chu kỳ 2–3) và không nằm trong file này.

Lớp: **U** Unit · **I** API tích hợp · **E** E2E Playwright · **Q** Chất lượng (Claude thật) · **P** Hiệu năng.

## 3. Chi tiết từng test case

### TC-001

**Tải 1 PDF hợp lệ → API nhận, tạo dòng documents trạng thái uploaded**

| | |
|---|---|
| AC | AC-US001-1a |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/documents/test_upload.py::test_single_pdf_ok` |
| Lệnh chạy | `docker compose exec api pytest tests/documents/test_upload.py::test_single_pdf_ok` |
| Cho trước | Lan đã đăng nhập, đã xác nhận phân loại |
| Khi | POST /doc-sets/{dsid}/documents với 1 PDF 2 trang |

**PASS khi** (tất cả đúng):

- `r.status == 200`
- `len(r.json) == 1 and r.json[0].status == "uploaded" and r.json[0].error_code is None and r.json[0].id is not None`
- `DB documents[id].status == "uploaded" and pages is None and uploaded_by == lan.id`
- `file tại doc.file_path có bytes == bytes đã gửi`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-002

**Worker xử lý tài liệu uploaded → ready, progress 100, pages đúng**

| | |
|---|---|
| AC | AC-US001-1a |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/ingestion/test_worker.py::test_worker_happy_path` |
| Lệnh chạy | `docker compose exec api pytest tests/ingestion/test_worker.py::test_worker_happy_path` |
| Cho trước | 1 tài liệu uploaded, PDF 2 trang có chữ |
| Khi | claim_next_document() rồi process_document() |

**PASS khi** (tất cả đúng):

- `(doc.status, doc.progress, doc.pages, doc.error_code) == ("ready", 100, 2, None)`
- `{c.page_number for c in chunks} == {1, 2}`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-003

**Biên trên — PDF đúng 200 trang và PDF đúng 20 971 520 byte được nhận và tới ready**

| | |
|---|---|
| AC | AC-US001-1a |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/documents/test_upload.py::test_upper_bounds_accepted` |
| Lệnh chạy | `docker compose exec api pytest tests/documents/test_upload.py::test_upper_bounds_accepted` |
| Cho trước | pdf_200 = make_pdf(200 trang, mỗi trang ≥ 40 ký tự) pdf_20m = make_pdf(2 trang) + phần đệm sau %%EOF sao cho len == 20_971_520 |
| Khi | tải từng file, chạy process_document cho mỗi id |

**PASS khi** (tất cả đúng):

- `với cả 2 file - r.status == 200 and r.json[0].status == "uploaded" and r.json[0].error_code is None`
- `pdf_200 - doc.status == "ready" and doc.pages == 200`
- `pdf_20m - doc.status == "ready" and doc.size_bytes == 20971520`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-004

**UI — tải PDF qua hộp xác nhận, dòng tài liệu tự chuyển "Sẵn sàng" không tải lại trang**

| | |
|---|---|
| AC | AC-US001-1a |
| Lớp · hồ sơ | E · FAKE |
| Mã test | `web/e2e/upload.spec.ts › Lan: xác nhận phân loại → tải PDF → Đang xử lý → Sẵn sàng` |
| Lệnh chạy | `cd web && npx playwright test -c e2e/playwright.config.ts upload.spec.ts -g "Lan: xác nhận phân loại" --repeat-each=3` |
| Cho trước | seed --reset; Lan đăng nhập; bộ tài liệu trống |
| Khi | chọn HopDongKhung.pdf (3 trang), xác nhận phân loại |

**PASS khi** (tất cả đúng):

- `docRow('HopDongKhung.pdf') hiển thị`
- `docRow có chữ 'Sẵn sàng' trong ≤ 60 s, không có page.reload() / page.goto() sau khi chọn file`
- `docRow chứa '3 trang'`

**Điều kiện máy đọc:** `exit_code == 0 với --repeat-each=3`

**FAIL khi:** bất kỳ mệnh đề trên sai ở bất kỳ lần lặp nào trong 3.

### TC-005

**Chuỗi trạng thái quan sát được là dãy con của uploaded → processing → ready**

| | |
|---|---|
| AC | AC-US001-1a |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `eval/measure_ingest.py` |
| Lệnh chạy | `docker compose exec api python /eval/measure_ingest.py --pages 3 --runs 1 --poll 0.2 --json /eval/reports/ingest-fake.json` |
| Cho trước | seed --reset; worker đang chạy; Lan đã xác nhận phân loại |
| Khi | tải 1 PDF 3 trang, poll GET /doc-sets/{dsid}/documents mỗi 0,2 s tới khi ready/failed hoặc 60 s |

**PASS khi** (tất cả đúng):

- `statuses (đã bỏ các giá trị lặp liên tiếp) là dãy con của ['uploaded', 'processing', 'ready']`
- `progress không giảm giữa hai lần poll liên tiếp`
- `trạng thái cuối == 'ready' and progress == 100 and pages == 3`

**Điều kiện máy đọc:** `json.runs[0].sequence_ok and json.runs[0].progress_monotonic and json.runs[0].final == 'ready'`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-006

**NFR-003 — PDF 50 trang tới ready ≤ 120 s, 3/3 lần**

| | |
|---|---|
| AC | AC-US001-1b |
| Lớp · hồ sơ | P · REAL |
| Mã test | `eval/measure_ingest.py` |
| Lệnh chạy | `docker compose exec api python /eval/measure_ingest.py --pages 50 --runs 3 --poll 1 --json /eval/reports/ingest-50.json` |
| Cho trước | model bge-m3 đã nạp (worker đã xử lý xong ≥ 1 file trước đó); không có tài liệu nào khác đang chờ; máy tham chiếu (OI-T3) |
| Khi | mỗi lần - seed --reset, tải 1 PDF 50 trang chữ dày (~1 500 ký tự/trang), đo t = lúc thấy ready − lúc API trả 200 |

**PASS khi** (tất cả đúng):

- `len(runs) == 3`
- `all(r.final == 'ready' for r in runs)`
- `all(r.seconds_to_ready <= 120 for r in runs)`
- `báo cáo ghi CPU, RAM, GPU (có/không), commit`

**Điều kiện máy đọc:** `json.all_pass == true`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-007

**NFR-003 — PDF 200 trang tới ready ≤ 480 s, 3/3 lần**

| | |
|---|---|
| AC | AC-US001-1b |
| Lớp · hồ sơ | P · REAL |
| Mã test | `eval/measure_ingest.py` |
| Lệnh chạy | `docker compose exec api python /eval/measure_ingest.py --pages 200 --runs 3 --poll 1 --json /eval/reports/ingest-200.json` |
| Cho trước | như TC-006 |
| Khi | như TC-006 với PDF 200 trang |

**PASS khi** (tất cả đúng):

- `len(runs) == 3`
- `all(r.final == 'ready' for r in runs)`
- `all(r.seconds_to_ready <= 480 for r in runs)`

**Điều kiện máy đọc:** `json.all_pass == true`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-008

**API — bộ có 2 file ready, hỏi thông tin chỉ có ở file F → trích dẫn F**

| | |
|---|---|
| AC | AC-US001-2 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_answer_cites_only_source_file` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_answer_cites_only_source_file` |
| Cho trước | HopDongKhung.pdf ready, chunk tr.14 = "Thời hạn thanh toán là 30 ngày…" BaoGia_v3.pdf ready, chunk tr.1 = "Gói phần mềm bản quyền giá 450.000.000 đồng." FakeLlmClient mặc định (trích search result đầu tiên) |
| Khi | hỏi "Giá gói phần mềm bản quyền trong báo giá là bao nhiêu?" |

**PASS khi** (tất cả đúng):

- `done.answer_type == "answered"`
- `len(done.citations) >= 1`
- `any(c.filename == "BaoGia_v3.pdf" for c in done.citations)`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-009

**UI — Lan tải 2 file, hỏi về báo giá → có nút "Nguồn n - BaoGia_v3.pdf"**

| | |
|---|---|
| AC | AC-US001-2 |
| Lớp · hồ sơ | E · FAKE |
| Mã test | `web/e2e/backbone.spec.ts › TC-009 câu hỏi về file vừa tải trích dẫn đúng file` |
| Lệnh chạy | `cd web && npx playwright test -c e2e/playwright.config.ts backbone.spec.ts -g "TC-009" --repeat-each=3` |
| Cho trước | seed --reset; Lan uploadOneByOne([CONTRACT, QUOTE]) — cả hai "Sẵn sàng" |
| Khi | ask("Giá gói phần mềm bản quyền trong báo giá là bao nhiêu?") |

**PASS khi** (tất cả đúng):

- `lastAnswer có ≥ 1 button tên khớp /^Nguồn \d+: BaoGia_v3\.pdf trang 1$/`
- `lastAnswer .sources chứa 'BaoGia_v3.pdf · trang 1'`

**Điều kiện máy đọc:** `exit_code == 0 với --repeat-each=3`

**FAIL khi:** bất kỳ mệnh đề trên sai ở bất kỳ lần lặp nào trong 3.

### TC-010

**Claude thật — câu Q04 (chỉ có trong BaoGia_v3.pdf) trả đúng giá trị và trích dẫn đúng file/trang**

| | |
|---|---|
| AC | AC-US001-2 |
| Lớp · hồ sơ | Q · REAL |
| Mã test | `eval/run_eval.py (câu Q04 trong eval/questions.yaml)` |
| Lệnh chạy | `docker compose exec api python /eval/run_eval.py` |
| Cho trước | corpus eval/corpus/ đủ 6 file, tất cả ready trong bộ "Eval" |
| Khi | hỏi Q04 "Giá gói phần mềm bản quyền trong báo giá phiên bản 3 là bao nhiêu?" |

**PASS khi** (tất cả đúng):

- `Q04.answer_type == "answered"`
- `'450.000.000' ∈ normalize(answer)  (normalize của run_eval.py)`
- `{file: 'BaoGia_v3.pdf', page: 1} ∈ Q04.citations`

**Điều kiện máy đọc:** `json.rows['Q04'].passed and json.rows['Q04'].citations_ok`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-011

**API — tài liệu processing được liệt kê trong pending_documents**

| | |
|---|---|
| AC | AC-US001-3 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_ask_pending_documents` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_ask_pending_documents` |
| Cho trước | HopDongKhung.pdf ready; BaoGia_v3.pdf processing |
| Khi | hỏi câu mặc định |

**PASS khi** (tất cả đúng):

- `done.pending_documents == [{"id": str(BaoGia.id), "filename": "BaoGia_v3.pdf"}]`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-012

**API — pending_documents = đúng tập uploaded ∪ processing; không có failed; không trích dẫn file pending; áp dụng cả not_found**

| | |
|---|---|
| AC | AC-US001-3 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_pending_documents_exact_set` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_pending_documents_exact_set` |
| Cho trước | A.pdf ready (có chunk); B.pdf uploaded; C.pdf processing; D.pdf failed (B, C có chunk cũ cùng nội dung với A để bẫy truy vấn) |
| Khi | (1) hỏi câu có trong A; (2) hỏi "Thủ đô của Pháp là gì?" |

**PASS khi** (tất cả đúng):

- `(1) {d.filename for d in done.pending_documents} == {'B.pdf', 'C.pdf'}`
- `(1) not any(c.document_id in {B.id, C.id, D.id} for c in done.citations)`
- `(2) done.answer_type == 'not_found' and {d.filename for d in done.pending_documents} == {'B.pdf', 'C.pdf'}`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-013

**Component — có pending_documents thì hiện ghi chú kèm tên file**

| | |
|---|---|
| AC | AC-US001-3 |
| Lớp · hồ sơ | U · none |
| Mã test | `web/src/components/AnswerCard.test.tsx › pending_documents → ghi chú tài liệu chưa dùng` |
| Lệnh chạy | `docker compose exec web npx vitest run src/components/AnswerCard.test.tsx -t "pending_documents"` |

**PASS khi** (tất cả đúng):

- `có text khớp /chưa được dùng để trả lời vì đang xử lý/`
- `có text 'BaoGia_v3.pdf'`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-014

**UI — file đang chờ xử lý được nêu trong ghi chú của câu trả lời**

| | |
|---|---|
| AC | AC-US001-3 |
| Lớp · hồ sơ | E · FAKE |
| Mã test | `web/e2e/backbone.spec.ts › TC-014 câu trả lời ghi chú file chưa sẵn sàng` |
| Lệnh chạy | `cd web && npx playwright test -c e2e/playwright.config.ts backbone.spec.ts -g "TC-014" --repeat-each=3` |
| Cho trước | seed --reset; Lan uploadOneByOne([CONTRACT]) → "Sẵn sàng"; `docker compose stop worker`; Lan tải QUOTE → dòng hiện "Đã tải lên" |
| Khi | ask("Thời hạn thanh toán là bao lâu?"); sau test luôn `docker compose start worker` (afterEach) |

**PASS khi** (tất cả đúng):

- `lastAnswer .pending-note hiển thị và chứa 'BaoGia_v3.pdf'`
- `lastAnswer không có button tên khớp /BaoGia_v3\.pdf/`

**Điều kiện máy đọc:** `exit_code == 0 với --repeat-each=3`

**FAIL khi:** bất kỳ mệnh đề trên sai ở bất kỳ lần lặp nào trong 3.

### TC-015

**Component — nút "Xác nhận và tải lên" bị vô hiệu tới khi tích ô**

| | |
|---|---|
| AC | AC-US001-4 |
| Lớp · hồ sơ | U · none |
| Mã test | `web/src/components/ClassificationDialog.test.tsx › nút chính bị vô hiệu tới khi tích xác nhận` |
| Lệnh chạy | `docker compose exec web npx vitest run src/components/ClassificationDialog.test.tsx -t "vô hiệu"` |

**PASS khi** (tất cả đúng):

- `nút chính disabled khi chưa tích`
- `nút chính enabled sau khi tích`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-016

**API — chưa xác nhận phân loại thì 409 và không tạo tài liệu; xác nhận ghi đúng 1 dòng nhật ký**

| | |
|---|---|
| AC | AC-US001-4 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/documents/test_upload.py::test_requires_classification` |
| Lệnh chạy | `docker compose exec api pytest tests/documents/test_upload.py::test_requires_classification` |
| Cho trước | Lan đăng nhập, phiên chưa xác nhận |
| Khi | tải 1 PDF; rồi xác nhận; rồi tải lại |

**PASS khi** (tất cả đúng):

- `lần 1 - r.status == 409 and r.json.code == "CLASSIFICATION_REQUIRED"`
- `lần 1 - count(documents) == 0`
- `sau xác nhận - count(audit_log where action='classification_confirm' and user_id=lan and doc_set_id=dsid) == 1`
- `lần 2 - r.status == 200`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-017

**UI — lần tải đầu trong phiên mới luôn hiện hộp xác nhận, nút khóa tới khi tích**

| | |
|---|---|
| AC | AC-US001-4 |
| Lớp · hồ sơ | E · FAKE |
| Mã test | `web/e2e/upload.spec.ts › 2 test đầu (mỗi test là 1 browser context = 1 phiên mới), qua helper confirmClassification` |
| Lệnh chạy | `cd web && npx playwright test -c e2e/playwright.config.ts upload.spec.ts -g "Lan: xác nhận phân loại|.docx và PDF hỏng" --repeat-each=3` |

**PASS khi** (tất cả đúng):

- `ở cả 2 phiên - dialog 'Xác nhận phân loại tài liệu' hiển thị`
- `nút 'Xác nhận và tải lên' disabled trước khi tích checkbox`
- `sau khi bấm - dialog ẩn`

**Điều kiện máy đọc:** `exit_code == 0 với --repeat-each=3`

**FAIL khi:** bất kỳ mệnh đề trên sai ở bất kỳ lần lặp nào trong 3.

### TC-018

**UI — lần tải thứ hai trong cùng phiên không hiện lại hộp xác nhận**

| | |
|---|---|
| AC | AC-US001-4 |
| Lớp · hồ sơ | E · FAKE |
| Mã test | `web/e2e/backbone.spec.ts › TC-018 không hỏi lại xác nhận trong cùng phiên` |
| Lệnh chạy | `cd web && npx playwright test -c e2e/playwright.config.ts backbone.spec.ts -g "TC-018" --repeat-each=3` |
| Cho trước | seed --reset; Lan đăng nhập; tải CONTRACT qua hộp xác nhận |
| Khi | chọn QUOTE trong cùng page |

**PASS khi** (tất cả đúng):

- `dialog 'Xác nhận phân loại tài liệu' có count == 0 trong suốt 2 s sau khi chọn file`
- `docRow('BaoGia_v3.pdf') hiển thị`

**Điều kiện máy đọc:** `exit_code == 0 với --repeat-each=3`

**FAIL khi:** bất kỳ mệnh đề trên sai ở bất kỳ lần lặp nào trong 3.

### TC-019

**API — câu trả lời answered có trích dẫn với filename, page, document_id**

| | |
|---|---|
| AC | AC-US009-1 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_ask_happy_path_event_order` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_ask_happy_path_event_order` |

**PASS khi** (tất cả đúng):

- `ev[0].name == "answer.started" and ev[-1].name == "answer.completed"`
- `done.answer_type == "answered"`
- `(done.citations[0].idx, filename, page, document_id) == (1, "HopDongKhung.pdf", 14, doc.id)`
- `tập citation_id trong các answer.delta == tập citation_id trong done`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-020

**API — bất biến - answered ⇒ ≥ 1 trích dẫn, filename ≠ "", 1 ≤ page ≤ documents.pages**

| | |
|---|---|
| AC | AC-US009-1 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_answered_citation_invariants` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_answered_citation_invariants` |
| Cho trước | tài liệu 3 trang đi qua worker thật (process_document + FakeEmbedder) để pages và chunk.page_number là dữ liệu thật |
| Khi | hỏi 3 câu có trong tài liệu (mỗi câu ứng với 1 trang) |

**PASS khi** (tất cả đúng):

- `với mỗi câu - done.answer_type == 'answered' and len(done.citations) >= 1`
- `với mỗi trích dẫn c - c.filename != '' and isinstance(c.page, int) and 1 <= c.page <= documents[c.document_id].pages`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-021

**Component — answered hiện [1] trong thân và danh sách Nguồn**

| | |
|---|---|
| AC | AC-US009-1 |
| Lớp · hồ sơ | U · none |
| Mã test | `web/src/components/AnswerCard.test.tsx › answered: nội dung, [1], nguồn, sao chép, đánh giá` |
| Lệnh chạy | `docker compose exec web npx vitest run src/components/AnswerCard.test.tsx -t "answered"` |

**PASS khi** (tất cả đúng):

- `có nút trích dẫn [1]`
- `có danh sách nguồn với tên file và trang`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-022

**UI — câu trả lời có nút "Nguồn 1 - <file> trang <p>" và danh sách nguồn**

| | |
|---|---|
| AC | AC-US009-1 |
| Lớp · hồ sơ | E · FAKE |
| Mã test | `web/e2e/chat.spec.ts › hỏi → stream → [1] → popover → mở PDF đúng trang` |
| Lệnh chạy | `cd web && npx playwright test -c e2e/playwright.config.ts chat.spec.ts -g "hỏi → stream" --repeat-each=3` |

**PASS khi** (tất cả đúng):

- `lastAnswer có button tên khớp /^Nguồn 1: HopDongKhung\.pdf trang \d+$/`
- `lastAnswer .sources chứa 'HopDongKhung.pdf · trang'`

**Điều kiện máy đọc:** `exit_code == 0 với --repeat-each=3`

**FAIL khi:** bất kỳ mệnh đề trên sai ở bất kỳ lần lặp nào trong 3.

### TC-023

**Claude thật — mọi lượt answered của bộ eval có ≥ 1 trích dẫn đủ file và trang**

| | |
|---|---|
| AC | AC-US009-1 |
| Lớp · hồ sơ | Q · REAL |
| Mã test | `eval/run_eval.py (đọc JSON sau khi chạy)` |
| Lệnh chạy | `docker compose exec api python /eval/run_eval.py` |

**PASS khi** (tất cả đúng):

- `answered = [r for r in json.rows if r.answer_type == 'answered']; len(answered) >= 1`
- `all(len(r.citations) >= 1 for r in answered)`
- `all(c.file != '' and c.page >= 1 for r in answered for c in r.citations)`

**Điều kiện máy đọc:** `json.checks.citation_present_all == true`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-024

**API — GET /citations/{id} trả snippet 1–300 ký tự, filename/page/document_id trùng SSE**

| | |
|---|---|
| AC | AC-US009-2 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_get_citation_ok_removed_forbidden (phần 200)` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_get_citation_ok_removed_forbidden` |

**PASS khi** (tất cả đúng):

- `r.status == 200`
- `(body.filename, body.page, body.document_id) == ("HopDongKhung.pdf", 14, doc.id)`
- `0 < len(body.snippet) <= 300`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-025

**Unit — snippet bị cắt tối đa 300 ký tự**

| | |
|---|---|
| AC | AC-US009-2 |
| Lớp · hồ sơ | U · none |
| Mã test | `backend/tests/qa/test_citation_filter.py::test_snippet_max_300` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_citation_filter.py::test_snippet_max_300` |

**PASS khi** (tất cả đúng):

- `cited_text dài > 300 → len(citation.snippet) == 300`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-026

**Component — bấm [1] mở popover có đoạn trích**

| | |
|---|---|
| AC | AC-US009-2 |
| Lớp · hồ sơ | U · none |
| Mã test | `web/src/components/AnswerCard.test.tsx › bấm [1] mở popover có đoạn trích; Esc đóng và trả focus` |
| Lệnh chạy | `docker compose exec web npx vitest run src/components/AnswerCard.test.tsx -t "popover"` |

**PASS khi** (tất cả đúng):

- `popover hiển thị đoạn trích trả về từ API`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-027

**UI — popover hiện "<file> · trang <p>" và đoạn trích**

| | |
|---|---|
| AC | AC-US009-2 |
| Lớp · hồ sơ | E · FAKE |
| Mã test | `web/e2e/chat.spec.ts › hỏi → stream → [1] → popover → mở PDF đúng trang` |
| Lệnh chạy | `cd web && npx playwright test -c e2e/playwright.config.ts chat.spec.ts -g "hỏi → stream" --repeat-each=3` |

**PASS khi** (tất cả đúng):

- `dialog hiển thị sau khi bấm [1]`
- `dialog .popover-quote chứa 'thanh toan'`
- `dialog chứa 'HopDongKhung.pdf · trang {p}' với p lấy từ tên nút 'Nguồn 1: HopDongKhung.pdf trang {p}'`

**Điều kiện máy đọc:** `exit_code == 0 với --repeat-each=3`

**FAIL khi:** bất kỳ mệnh đề trên sai ở bất kỳ lần lặp nào trong 3.

### TC-028

**Claude thật — 100% đoạn trích nằm trên đúng trang đã nêu**

| | |
|---|---|
| AC | AC-US009-3a |
| Lớp · hồ sơ | Q · REAL |
| Mã test | `eval/check_grounding.py` |
| Lệnh chạy | `docker compose exec api python /eval/check_grounding.py --run /eval/reports/<ngày>.json   (ghi <ngày>-grounding.json)` |
| Cho trước | vừa chạy xong run_eval.py (TC-010) ở hồ sơ REAL; DB chưa reset |
| Khi | với mỗi citation_id của mọi lượt answered - đọc snippet, page, document.file_path từ DB; trích page_text |

**PASS khi** (tất cả đúng):

- `turns_checked >= 16`
- `violations == [] với violation = norm(snippet) not in norm(page_text(doc, page))`

**Điều kiện máy đọc:** `json.turns_checked >= 16 and len(json.violations) == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-029

**API — đoạn trích nằm trên đúng trang (hồ sơ FAKE, chạy mỗi lần CI)**

| | |
|---|---|
| AC | AC-US009-3a |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_snippet_is_on_cited_page` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_snippet_is_on_cited_page` |
| Cho trước | PDF 3 trang (pdf_factory) đi qua worker thật; mỗi trang một sự kiện khác nhau |
| Khi | hỏi 3 câu, mỗi câu nhắm 1 trang |

**PASS khi** (tất cả đúng):

- `với mọi trích dẫn - norm(Citation.snippet) in norm(page_text(doc, Citation.page))`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-030

**Người chấm — đoạn trích hỗ trợ đúng nội dung câu trả lời (100% yes)**

| | |
|---|---|
| AC | AC-US009-3b |
| Lớp · hồ sơ | Q · REAL |
| Mã test | `eval/reports/<ngày>-grounding-review.csv` |
| Lệnh chạy | `docker compose exec api python /eval/check_grounding.py --run /eval/reports/<ngày>.json --export-review → người chấm điền cột supports → docker compose exec api python /eval/check_grounding.py --run /eval/reports/<ngày>.json --score-review` |
| Cho trước | cùng lượt chạy với TC-028 |
| Rubric | Chỉ dựa vào snippet, có suy ra được đúng nội dung của span_text không? yes \| no. Không chắc → no. |

**PASS khi** (tất cả đúng):

- `số dòng CSV == số cặp (span có trích dẫn, trích dẫn) trong lượt chạy`
- `mọi dòng supports ∈ {'yes', 'no'} (không ô trống)`
- `count(supports == 'no') == 0`

**Điều kiện máy đọc:** `--score-review in JSON có pass == true (rows == expected_rows, blank_or_invalid == 0, no_count == 0); exit code 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-031

**Unit — khối không có trích dẫn hợp lệ bị loại (đầu, cuối, giữa không phải câu nối, index ngoài phạm vi)**

| | |
|---|---|
| AC | AC-US009-4 |
| Lớp · hồ sơ | U · none |
| Mã test | `backend/tests/qa/test_citation_filter.py::{test_uncited_leading_block_dropped, test_uncited_trailing_block_dropped, test_non_connective_between_dropped, test_out_of_range_index_ignored}` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_citation_filter.py -k "uncited_leading or uncited_trailing or non_connective_between or out_of_range"` |

**PASS khi** (tất cả đúng):

- `text của khối không nguồn không có trong spans đã trả và không có trong finalize().answer_text`

**Điều kiện máy đọc:** `exit_code == 0 và 4 test được chọn (không phải 0)`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-032

**Unit — câu nối ngắn giữa hai khối có nguồn được giữ (ngoại lệ đã ghi trong AC)**

| | |
|---|---|
| AC | AC-US009-4 |
| Lớp · hồ sơ | U · none |
| Mã test | `backend/tests/qa/test_citation_filter.py::{test_connective_between_cited_kept, test_is_connective_cases}` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_citation_filter.py -k "connective_between_cited_kept or is_connective_cases"` |

**PASS khi** (tất cả đúng):

- `câu nối nằm giữa 2 khối có nguồn xuất hiện trong span với citations == ()`
- `is_connective đúng theo bảng tham số (≤ 12 từ, không chữ số, < 30% từ viết hoa)`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-033

**Unit — không khối nào có nguồn → not_found**

| | |
|---|---|
| AC | AC-US009-4 |
| Lớp · hồ sơ | U · none |
| Mã test | `backend/tests/qa/test_citation_filter.py::{test_all_uncited_is_not_found, test_marker_only_is_not_found}` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_citation_filter.py -k "all_uncited_is_not_found or marker_only_is_not_found"` |

**PASS khi** (tất cả đúng):

- `finalize() == FilterResult("not_found", (), "", ())`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-034

**API — khối bịa không nguồn không tới người dùng và không được lưu**

| | |
|---|---|
| AC | AC-US009-4 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_uncited_blocks_never_streamed_or_saved` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_uncited_blocks_never_streamed_or_saved` |
| Cho trước | llm.script = [TextBlock("Theo kinh nghiệm thường là 99 ngày.", ()),               TextBlock("Thời hạn là 30 ngày.", (RawCitation(0, "30 ngày"),)),               TextBlock("Có thể kéo dài tới 7 ngày nữa theo Luật Thương mại.", ()),               AnswerDone("end_turn", 1, 1)] |
| Khi | hỏi câu mặc định |

**PASS khi** (tất cả đúng):

- `streamed = ''.join(d.text for d in ev if name == 'answer.delta')`
- `'99 ngày' not in streamed and '7 ngày' not in streamed and '30 ngày' in streamed`
- `turn.answer == streamed`
- `done.answer_type == 'answered'`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.

### TC-035

**API — mọi khối không nguồn → not_found, không có delta, answer rỗng**

| | |
|---|---|
| AC | AC-US009-4 |
| Lớp · hồ sơ | I · FAKE |
| Mã test | `backend/tests/qa/test_ask_api.py::test_all_uncited_becomes_not_found` |
| Lệnh chạy | `docker compose exec api pytest tests/qa/test_ask_api.py::test_all_uncited_becomes_not_found` |
| Cho trước | llm.script = [TextBlock("Thời hạn là 30 ngày.", ()), AnswerDone("end_turn", 1, 1)] |
| Khi | hỏi câu mặc định |

**PASS khi** (tất cả đúng):

- `[name for name, _ in ev] == ['answer.started', 'answer.completed']`
- `done.answer_type == 'not_found' and done.citations == []`
- `turn.answer == '' and turn.answer_type == 'not_found'`

**Điều kiện máy đọc:** `exit_code == 0`

**FAIL khi:** bất kỳ mệnh đề trên sai.
