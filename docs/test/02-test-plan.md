# Test plan — Đường xương sống "Tải PDF → câu trả lời có trích dẫn"

| Phiên bản | Ngày | Phạm vi code | AC | Ma trận | PASS/FAIL |
|---|---|---|---|---|---|
| 0.1 | 2026-10-28 | commit `20031fe` | [01-pham-vi-va-ac.md](01-pham-vi-va-ac.md) | [03-ma-tran-ac-tc.md](03-ma-tran-ac-tc.md) | [test-cases.yaml](test-cases.yaml) |

**Mục tiêu.** Chứng minh bằng bằng chứng máy đọc được rằng một Thành viên tải được 1 PDF tới "Sẵn sàng" (US-001) và nhận câu trả lời mà **mọi trích dẫn trỏ đúng tài liệu, đúng trang, có đoạn trích nằm trên trang đó** (US-009). Kết quả: mỗi AC trong phạm vi có verdict PASS/FAIL.

**Phạm vi.** 10 AC đã chốt: AC-US001-1a, 1b, 2, 3, 4 và AC-US009-1, 2, 3a, 3b, 4. 35 test case, mỗi TC trỏ về ít nhất 1 AC.

**Non-goals (không kiểm trong đợt này).**
- Chất lượng câu trả lời theo thống kê: US-006 (p90 ≤ 5 s, ≥ 80% SC-01), US-007, US-008, US-010, US-011 — `run_eval.py` vẫn chạy nhưng chỉ dùng các chỉ số phục vụ AC-US001-2 và AC-US009-*.
- File không được tiếp nhận (US-004), tải lô (US-002), trùng tên (E-09), đầy 50 file (E-08).
- Phân quyền và quản trị (US-012/013/014/020/021/022), Dừng/Sao chép/Đánh giá/Mở PDF (US-015/017/018/019).
- DoD chung: a11y bằng bàn phím, axe-core, độ phủ ≥ 80%, contract test OpenAPI.
- Tải 10 người đồng thời (NFR-005), bảo mật, trình duyệt khác Chromium.

Các test hiện có của những phần trên **vẫn chạy như regression** nhưng không tính vào verdict của đợt này.

**Chiến lược phân lớp.**

| Lớp | Công cụ | Hồ sơ | Kiểm cái gì | Vì sao ở lớp này |
|---|---|---|---|---|
| **U** — unit | pytest (`citation_filter`), Vitest (component) | — | Quy tắc lọc trích dẫn, hiển thị `[n]`/popover/ghi chú, hộp xác nhận | Nhanh, xác định; bao các nhánh khó dựng qua API |
| **I** — API tích hợp | pytest + httpx + DB `cwd_test`, `FakeLlmClient` có kịch bản | FAKE | Hợp đồng SSE, `pending_documents`, 409, worker → `ready`, đoạn trích nằm trên trang | Kiểm được bất biến dữ liệu mà UI không lộ ra |
| **E** — end-to-end | Playwright, Chromium 1440×900 | FAKE | Người dùng thấy đúng: "Sẵn sàng" không tải lại trang, nút `Nguồn n`, popover, ghi chú | Chứng minh 3 tiến trình nối đúng |
| **Q** — chất lượng | `eval/run_eval.py` + `eval/check_grounding.py` + CSV người chấm | REAL | Trích dẫn đúng file/trang với Claude thật; đoạn trích có trên trang; ngữ nghĩa | Chỉ Claude thật mới cho `cited_text` thật |
| **P** — hiệu năng | `eval/measure_ingest.py` | REAL | NFR-003 cho 50 và 200 trang | Cần bge-m3 thật |

Thứ tự chạy: U → I → E → Q → P. Lớp dưới đỏ thì không chạy lớp trên.

**Môi trường & dữ liệu.**

| Hồ sơ | Biến `.env` | Dùng cho |
|---|---|---|
| FAKE | `LLM_FAKE=1`, `EMBED_FAKE=1`, `RETRIEVAL_NOT_FOUND_TAU=0.25` | U, I, E — miễn phí, xác định |
| REAL | `LLM_FAKE=0`, `EMBED_FAKE=0`, `ANTHROPIC_API_KEY`, τ mặc định 0,35, `LLM_MODEL=claude-opus-5-5` | Q, P — ghi lại τ, model, cấu hình máy trong báo cáo |

- Docker Compose local: web http://localhost:5173, API http://localhost:8000/api/v1, PostgreSQL `localhost:5432` (`cwd`/`cwd`, DB test `cwd_test`).
- Tài khoản: `lan@demo.local` (Thành viên, người chạy chính), `minh@demo.local` (người chạy eval). Đặt lại dữ liệu trước mỗi spec/lượt: `docker compose exec -T api python -m app.seed --reset`.
- Dữ liệu có sẵn: fixture e2e `web/e2e/fixtures/pdf.ts`, `backend/tests/pdf_factory.py`, corpus `eval/corpus/` (6 PDF), `eval/questions.yaml` (20 câu).
- Dữ liệu cần sinh (trong code, không commit nhị phân): PDF **200 trang**, PDF **đúng 20 971 520 byte**, PDF **50 trang** và **200 trang** có chữ dày đặc cho P.

**Tiêu chí vào.** `docker compose up` khỏe; `ruff check .` sạch; mọi TC ở trạng thái `to-write` đã được viết và review đối chiếu khối `expect` trong `test-cases.yaml` **trước khi** chạy lần đầu.

**Tiêu chí thoát (tất cả phải đúng).**
1. Mỗi AC trong phạm vi có ≥ 1 TC, và **mọi** TC trỏ về AC đó có verdict `PASS`. Một TC `FAIL` hoặc `BLOCKED` ⇒ AC đó `FAIL`.
2. TC lớp E phải PASS **3/3 lần chạy liên tiếp**; không chấp nhận "chạy lại cho xanh".
3. Regression: toàn bộ `pytest`, `npm test`, `npm run e2e` xanh (không chỉ các TC trong phạm vi).
4. Lớp Q: TC-010, TC-023, TC-028 PASS; CSV TC-030 đủ dòng và 100% `yes`.
5. Lớp P: TC-006, TC-007 PASS trên máy tham chiếu đã chốt (OI-T3). Chưa chốt máy ⇒ AC-US001-1b ghi `không kết luận` và đợt này **không** thoát, trừ khi PO miễn bằng văn bản.
6. Không còn lỗi mức nghiêm trọng 1–2 mở trong phạm vi; mọi FAIL có ticket ghi nguyên nhân.
7. Báo cáo cuối `docs/test/reports/<ngày>.md`: verdict từng TC, từng AC, commit, hồ sơ, τ, model, máy.
