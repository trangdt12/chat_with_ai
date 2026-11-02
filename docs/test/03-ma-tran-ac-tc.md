# Ma trận AC ↔ test case

> ⚠️ **Đã được thay bằng [docs/test-cases.md](../test-cases.md)** (ma trận + định nghĩa PASS/FAIL, sinh tự động từ test-cases.yaml) và [docs/traceability.md](../traceability.md) (kết quả + bằng chứng).
> Giữ file này vì §2 (mã test đã thêm) và §3 (test không trỏ về AC trong phạm vi → regression) vẫn đúng. Cột trạng thái ✅ ở §1 nghĩa là "test đã có", **không** phải kết quả chạy.

> Nguồn sự thật: [test-cases.yaml](test-cases.yaml) — bảng này tóm tắt từ đó. Định nghĩa AC: [01-pham-vi-va-ac.md](01-pham-vi-va-ac.md).
> Quy tắc: **mọi AC có một dòng**; **mọi TC trỏ về ≥ 1 AC**. TC không trỏ về AC nào thì bị loại khỏi ma trận (giữ làm regression) hoặc phải mở AC mới — xem §3.
> Trạng thái: ✅ test đã có trong repo · 👤 người chấm. Kết quả chạy: [reports/2026-10-28.md](reports/2026-10-28.md).

## 1. Ma trận

| AC | U | I | E | Q | P | Đủ lớp? |
|---|---|---|---|---|---|---|
| **AC-US001-1a** tiếp nhận → ready | — | TC-001 ✅ · TC-002 ✅ · TC-003 ✅ · TC-005 ✅ | TC-004 ✅ | — | — | Có |
| **AC-US001-1b** NFR-003 | — | — | — | — | TC-006 ✅ · TC-007 ✅ | Có (chờ OI-T3) |
| **AC-US001-2** trích dẫn file vừa tải | — | TC-008 ✅ | TC-009 ✅ | TC-010 ✅ | — | Có |
| **AC-US001-3** ghi chú file chưa sẵn sàng | TC-013 ✅ | TC-011 ✅ · TC-012 ✅ | TC-014 ✅ | — | — | Có |
| **AC-US001-4** xác nhận phân loại | TC-015 ✅ | TC-016 ✅ | TC-017 ✅ · TC-018 ✅ | — | — | Có |
| **AC-US009-1** có trích dẫn file + trang | TC-021 ✅ | TC-019 ✅ · TC-020 ✅ | TC-022 ✅ | TC-023 ✅ | — | Có |
| **AC-US009-2** popover ≤ 300 ký tự | TC-025 ✅ · TC-026 ✅ | TC-024 ✅ | TC-027 ✅ | — | — | Có |
| **AC-US009-3a** đoạn trích nằm trên trang | — | TC-029 ✅ | — | TC-028 ✅ | — | Có |
| **AC-US009-3b** đoạn trích hỗ trợ câu trả lời | — | — | — | TC-030 👤 | — | Có |
| **AC-US009-4** bỏ thông tin không nguồn | TC-031 ✅ · TC-032 ✅ · TC-033 ✅ | TC-034 ✅ · TC-035 ✅ | — | — | — | Có |

**Tổng:** 10 AC · 35 TC (34 ✅, 1 👤). Không AC nào thiếu TC; không TC nào thiếu AC (đã kiểm bằng script đọc `test-cases.yaml`).

Vì sao một số ô để trống:
- AC-US001-1b chỉ ở P: với embedding giả thì thời gian không có ý nghĩa.
- AC-US009-3a không có E: UI không cho thấy text gốc của trang; kiểm ở I/Q chặt hơn.
- AC-US009-4 không có E: không điều khiển được FakeLlm theo kịch bản từ trình duyệt; bất biến đã kiểm ở I trên đúng dữ liệu SSE mà FE nhận.

## 2. Mã test đã thêm (2026-10-28)

| Việc | Ở đâu | TC |
|---|---|---|
| 7 test pytest mới | `backend/tests/documents/test_upload.py::test_upper_bounds_accepted`; `backend/tests/qa/test_ask_api.py::{test_answer_cites_only_source_file, test_pending_documents_exact_set, test_answered_citation_invariants, test_snippet_is_on_cited_page, test_uncited_blocks_never_streamed_or_saved, test_all_uncited_becomes_not_found}` | TC-003, 008, 012, 020, 029, 034, 035 |
| `make_pdf(pad=…)`, `make_pdf_of_size()` | `backend/tests/pdf_factory.py` | TC-003 |
| 3 test Playwright mới | `web/e2e/backbone.spec.ts`; helper `setWorker()` trong `web/e2e/helpers.ts` | TC-009, 014, 018 |
| Thêm assert | `test_requires_classification` (không tạo tài liệu khi 409; đúng 1 dòng nhật ký); chat.spec "hỏi → stream" (đầu popover có đúng file · trang) | TC-016, 027 |
| `run_eval.py` ghi thêm `<ngày>.json` (không có câu trả lời) và `<ngày>-spans.json` (cho người chấm, đã gitignore) | `eval/run_eval.py` | TC-010, 023, 028, 030 |
| Kiểm 3a, xuất và chấm CSV 3b | `eval/check_grounding.py` | TC-028, 030 |
| Sinh PDF n trang, tải lên, poll, xuất JSON | `eval/measure_ingest.py` | TC-005, 006, 007 |

## 3. Test có sẵn không trỏ về AC trong phạm vi

| Test | Trỏ về | Quyết định |
|---|---|---|
| `test_not_pdf_magic_bytes`, `test_too_large`, `UploadDropzone` "chặn .docx" / "chặn > 20 MB", upload.spec ".docx và PDF hỏng…" (phần thông báo lỗi), `test_worker_pdf_errors` | US-004 | Ngoài phạm vi — regression |
| `test_member_cannot_batch`, `test_batch_one_too_large_others_ok`, upload.spec "Lan chọn 2 file", batch.spec | US-002 | Ngoài phạm vi — regression |
| `test_concurrent_last_slot` | US-002 / E-08 | Ngoài phạm vi — regression |
| `test_admin_not_member_forbidden`, phần 403 của `test_get_citation_ok_removed_forbidden` | US-013 / US-014 | Ngoài phạm vi — regression |
| Phần 410 của `test_get_citation_ok_removed_forbidden`, AnswerCard "trích dẫn tới tài liệu đã gỡ" | US-020 | Ngoài phạm vi — regression |
| chat.spec phần "mở PDF đúng trang" | US-019 | Ngoài phạm vi — regression |
| `test_duplicate_name_renamed` | E-09, **không có AC** | **Mồ côi.** Loại khỏi ma trận. Đề xuất PO mở AC-US001-5 *"Tải file trùng tên → đổi thành `Ten (2).pdf`, file cũ giữ nguyên"* nếu muốn đưa vào phạm vi |
| `test_worker_rerun_idempotent`, `test_recover_stuck_processing`, `test_claim_skip_locked`, `test_worker_document_deleted_midway` | Độ bền worker, **không có AC** | **Mồ côi.** Loại khỏi ma trận, giữ regression. Đề xuất mở NFR/AC *"Worker khởi động lại không làm tài liệu kẹt ở Đang xử lý"* |
| chat.spec "bàn phím: Tab tới [1]…", ClassificationDialog "Esc…", "Tab không thoát…" | DoD (a11y), **không có AC** | Loại khỏi ma trận; thuộc kiểm DoD |
| `test_no_content_in_audit_meta` | DoD G-13 | Loại khỏi ma trận; thuộc kiểm DoD |
