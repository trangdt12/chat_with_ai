# Truy vết US ↔ AC ↔ TC ↔ bằng chứng

> **Sinh tự động** bằng `scripts/build_test_docs.py` từ kết quả thật trong `reports/<lượt>/` — không sửa tay. Định nghĩa PASS/FAIL: [test-cases.md](test-cases.md).

## 1. Các lượt chạy

| Lượt | Bắt đầu (UTC) | Commit | File chưa commit | Hồ sơ | CI | Bằng chứng |
|---|---|---|---|---|---|---|
| run-1 | 2026-11-02T15:40:59Z | `bdc310b` | 2 | FAKE | false  | [env](../reports/run-1/env.txt) · [exit codes](../reports/run-1/exit-codes.txt) · [Playwright](../playwright-report/run-1/index.html) · [docker log](../reports/run-1/docker-compose.log) |

Verdict cuối của TC: **PASS** ⇔ PASS ở mọi lượt (≥ 2); **FAIL** ⇔ FAIL ở ≥ 1 lượt; còn lại **BLOCKED**. Verdict AC: PASS ⇔ mọi TC của AC đó PASS.

## 2. Tổng hợp theo AC

| User story | AC | TC | Verdict AC |
|---|---|---|---|
| US-001 Tải một file PDF lên | AC-US001-1a | TC-001, TC-002, TC-003, TC-004, TC-005 | ⏸ BLOCKED |
| US-001 Tải một file PDF lên | AC-US001-1b | TC-006, TC-007 | ⏸ BLOCKED |
| US-001 Tải một file PDF lên | AC-US001-2 | TC-008, TC-009, TC-010 | ⏸ BLOCKED |
| US-001 Tải một file PDF lên | AC-US001-3 | TC-011, TC-012, TC-013, TC-014 | ⏸ BLOCKED |
| US-001 Tải một file PDF lên | AC-US001-4 | TC-015, TC-016, TC-017, TC-018 | ⏸ BLOCKED |
| US-009 Trích dẫn tên tài liệu và số trang | AC-US009-1 | TC-019, TC-020, TC-021, TC-022, TC-023 | ⏸ BLOCKED |
| US-009 Trích dẫn tên tài liệu và số trang | AC-US009-2 | TC-024, TC-025, TC-026, TC-027 | ⏸ BLOCKED |
| US-009 Trích dẫn tên tài liệu và số trang | AC-US009-3a | TC-028, TC-029 | ⏸ BLOCKED |
| US-009 Trích dẫn tên tài liệu và số trang | AC-US009-3b | TC-030 | ⏸ BLOCKED |
| US-009 Trích dẫn tên tài liệu và số trang | AC-US009-4 | TC-031, TC-032, TC-033, TC-034, TC-035 | ⏸ BLOCKED |

**TC:** 0 PASS · 0 FAIL · 35 BLOCKED / 35. **AC:** 0 PASS / 10.

## 3. Chi tiết US ↔ AC ↔ TC ↔ bằng chứng

| US | AC | TC | Lớp | Verdict run-1 | Ổn định | Verdict | Bằng chứng | Bug |
|---|---|---|---|---|---|---|---|---|
| US-001 | AC-US001-1a | [TC-001](test-cases.md#tc-001) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-1a | [TC-002](test-cases.md#tc-002) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-1a | [TC-003](test-cases.md#tc-003) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-1a | [TC-004](test-cases.md#tc-004) | E | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-1a | [TC-005](test-cases.md#tc-005) | I | ⏸ BLOCKED<br><sub>thiếu ingest-fake.json</sub> | — | ⏸ BLOCKED | thiếu ingest-fake.json | — |
| US-001 | AC-US001-1b | [TC-006](test-cases.md#tc-006) | P | ⏸ BLOCKED<br><sub>cần bge-m3 thật và máy tham chiếu (OI-T3) — không chạy trong CI</sub> | — | ⏸ BLOCKED | cần bge-m3 thật và máy tham chiếu (OI-T3) — không chạy trong CI | — |
| US-001 | AC-US001-1b | [TC-007](test-cases.md#tc-007) | P | ⏸ BLOCKED<br><sub>cần bge-m3 thật và máy tham chiếu (OI-T3) — không chạy trong CI</sub> | — | ⏸ BLOCKED | cần bge-m3 thật và máy tham chiếu (OI-T3) — không chạy trong CI | — |
| US-001 | AC-US001-2 | [TC-008](test-cases.md#tc-008) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-2 | [TC-009](test-cases.md#tc-009) | E | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-2 | [TC-010](test-cases.md#tc-010) | Q | ⏸ BLOCKED<br><sub>cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI</sub> | — | ⏸ BLOCKED | cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI | — |
| US-001 | AC-US001-3 | [TC-011](test-cases.md#tc-011) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-3 | [TC-012](test-cases.md#tc-012) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-3 | [TC-013](test-cases.md#tc-013) | U | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-3 | [TC-014](test-cases.md#tc-014) | E | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-4 | [TC-015](test-cases.md#tc-015) | U | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-4 | [TC-016](test-cases.md#tc-016) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-4 | [TC-017](test-cases.md#tc-017) | E | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-001 | AC-US001-4 | [TC-018](test-cases.md#tc-018) | E | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-1 | [TC-019](test-cases.md#tc-019) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-1 | [TC-020](test-cases.md#tc-020) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-1 | [TC-021](test-cases.md#tc-021) | U | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-1 | [TC-022](test-cases.md#tc-022) | E | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-1 | [TC-023](test-cases.md#tc-023) | Q | ⏸ BLOCKED<br><sub>cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI</sub> | — | ⏸ BLOCKED | cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI | — |
| US-009 | AC-US009-2 | [TC-024](test-cases.md#tc-024) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-2 | [TC-025](test-cases.md#tc-025) | U | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-2 | [TC-026](test-cases.md#tc-026) | U | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-2 | [TC-027](test-cases.md#tc-027) | E | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-3a | [TC-028](test-cases.md#tc-028) | Q | ⏸ BLOCKED<br><sub>cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI</sub> | — | ⏸ BLOCKED | cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI | — |
| US-009 | AC-US009-3a | [TC-029](test-cases.md#tc-029) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-3b | [TC-030](test-cases.md#tc-030) | Q | ⏸ BLOCKED<br><sub>cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI</sub> | — | ⏸ BLOCKED | cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI | — |
| US-009 | AC-US009-4 | [TC-031](test-cases.md#tc-031) | U | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-4 | [TC-032](test-cases.md#tc-032) | U | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-4 | [TC-033](test-cases.md#tc-033) | U | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-4 | [TC-034](test-cases.md#tc-034) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |
| US-009 | AC-US009-4 | [TC-035](test-cases.md#tc-035) | I | ⏸ BLOCKED<br><sub>không tìm thấy kết quả test hoặc test bị skip</sub> | — | ⏸ BLOCKED | không tìm thấy kết quả test hoặc test bị skip | — |

## 4. TC chưa chạy được (BLOCKED) và lý do

| TC | Lớp | Lý do | Cách chạy khi có điều kiện |
|---|---|---|---|
| TC-001 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/documents/test_upload.py::test_single_pdf_ok` |
| TC-002 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/ingestion/test_worker.py::test_worker_happy_path` |
| TC-003 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/documents/test_upload.py::test_upper_bounds_accepted` |
| TC-004 | E | không tìm thấy kết quả test hoặc test bị skip | `cd web && npx playwright test -c e2e/playwright.config.ts upload.spec.ts -g "Lan: xác nhận phân loại" --repeat-each=3` |
| TC-005 | I | thiếu ingest-fake.json | `docker compose exec api python /eval/measure_ingest.py --pages 3 --runs 1 --poll 0.2 --json /eval/reports/ingest-fake.json` |
| TC-006 | P | cần bge-m3 thật và máy tham chiếu (OI-T3) — không chạy trong CI | `docker compose exec api python /eval/measure_ingest.py --pages 50 --runs 3 --poll 1 --json /eval/reports/ingest-50.json` |
| TC-007 | P | cần bge-m3 thật và máy tham chiếu (OI-T3) — không chạy trong CI | `docker compose exec api python /eval/measure_ingest.py --pages 200 --runs 3 --poll 1 --json /eval/reports/ingest-200.json` |
| TC-008 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_answer_cites_only_source_file` |
| TC-009 | E | không tìm thấy kết quả test hoặc test bị skip | `cd web && npx playwright test -c e2e/playwright.config.ts backbone.spec.ts -g "TC-009" --repeat-each=3` |
| TC-010 | Q | cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI | `docker compose exec api python /eval/run_eval.py` |
| TC-011 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_ask_pending_documents` |
| TC-012 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_pending_documents_exact_set` |
| TC-013 | U | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec web npx vitest run src/components/AnswerCard.test.tsx -t "pending_documents"` |
| TC-014 | E | không tìm thấy kết quả test hoặc test bị skip | `cd web && npx playwright test -c e2e/playwright.config.ts backbone.spec.ts -g "TC-014" --repeat-each=3` |
| TC-015 | U | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec web npx vitest run src/components/ClassificationDialog.test.tsx -t "vô hiệu"` |
| TC-016 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/documents/test_upload.py::test_requires_classification` |
| TC-017 | E | không tìm thấy kết quả test hoặc test bị skip | `cd web && npx playwright test -c e2e/playwright.config.ts upload.spec.ts -g "Lan: xác nhận phân loại|.docx và PDF hỏng" --repeat-each=3` |
| TC-018 | E | không tìm thấy kết quả test hoặc test bị skip | `cd web && npx playwright test -c e2e/playwright.config.ts backbone.spec.ts -g "TC-018" --repeat-each=3` |
| TC-019 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_ask_happy_path_event_order` |
| TC-020 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_answered_citation_invariants` |
| TC-021 | U | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec web npx vitest run src/components/AnswerCard.test.tsx -t "answered"` |
| TC-022 | E | không tìm thấy kết quả test hoặc test bị skip | `cd web && npx playwright test -c e2e/playwright.config.ts chat.spec.ts -g "hỏi → stream" --repeat-each=3` |
| TC-023 | Q | cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI | `docker compose exec api python /eval/run_eval.py` |
| TC-024 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_get_citation_ok_removed_forbidden` |
| TC-025 | U | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_citation_filter.py::test_snippet_max_300` |
| TC-026 | U | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec web npx vitest run src/components/AnswerCard.test.tsx -t "popover"` |
| TC-027 | E | không tìm thấy kết quả test hoặc test bị skip | `cd web && npx playwright test -c e2e/playwright.config.ts chat.spec.ts -g "hỏi → stream" --repeat-each=3` |
| TC-028 | Q | cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI | `docker compose exec api python /eval/check_grounding.py --run /eval/reports/<ngày>.json   (ghi <ngày>-grounding.json)` |
| TC-029 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_snippet_is_on_cited_page` |
| TC-030 | Q | cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI | `docker compose exec api python /eval/check_grounding.py --run /eval/reports/<ngày>.json --export-review → người chấm điền cột supports → docker compose exec api python /eval/check_grounding.py --run /eval/reports/<ngày>.json --score-review` |
| TC-031 | U | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_citation_filter.py -k "uncited_leading or uncited_trailing or non_connective_between or out_of_range"` |
| TC-032 | U | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_citation_filter.py -k "connective_between_cited_kept or is_connective_cases"` |
| TC-033 | U | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_citation_filter.py -k "all_uncited_is_not_found or marker_only_is_not_found"` |
| TC-034 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_uncited_blocks_never_streamed_or_saved` |
| TC-035 | I | không tìm thấy kết quả test hoặc test bị skip | `docker compose exec api pytest tests/qa/test_ask_api.py::test_all_uncited_becomes_not_found` |
