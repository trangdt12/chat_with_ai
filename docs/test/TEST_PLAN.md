# Master Test Plan (IEEE 829-2008) — Công cụ "Chat với tài liệu" (MVP, bản thử nghiệm)

> **Chuẩn:** IEEE 829-2008 (Software and System Test Documentation) · tham chiếu IEEE 29119, ISO/IEC 25010
> **Prompt dùng để soạn:** `docs/TestPlan_IEEE 829-2008_prompt.md` v2.0 · **Checklist tự kiểm:** [Test_Plan_IEEE_829_Checklist.xlsx](Test_Plan_IEEE_829_Checklist.xlsx)
> **Kế hoạch con (đợt "đường xương sống"):** [02-test-plan.md](02-test-plan.md) · AC đã chốt: [01-pham-vi-va-ac.md](01-pham-vi-va-ac.md) · Ma trận: [03-ma-tran-ac-tc.md](03-ma-tran-ac-tc.md) · PASS/FAIL máy đọc: [test-cases.yaml](test-cases.yaml)
> ⚠️ Tài liệu bài tập. Mọi số liệu [GĐ] kế thừa giả định bài tập của BRD/PRD. Kế hoạch này **không chứa kết quả chạy**; kết quả nằm ở `docs/test/reports/` và RTM.

---

## 0. Kiểm soát tài liệu

| Thuộc tính | Giá trị |
|---|---|
| Plan identifier | **TP-CWD-001** |
| Phiên bản | 0.1 |
| Ngày phát hành | 2026-11-02 |
| Trạng thái | **Draft** — chờ review |
| Phân loại | Nội bộ |
| Owner | QA Lead *(chưa có tên người — OQ-TP-02)* |
| Người phê duyệt | Product Owner; Engineering Lead *(vai trò theo PRD-CWD-001 và SAD-CWD-001; tên người — OQ-TP-02)* |
| Đối tượng kiểm thử | Repo `chat_with_ai`, commit `20031fe` (2026-10-28) + mã test chưa commit của đợt xương sống |
| Đường dẫn đầu ra | `docs/test/TEST_PLAN.md` *(prompt đề xuất `docs/07-verification/TEST_PLAN.md`; repo dùng `docs/test/` — OQ-TP-01)* |

### 0.1 Tham số dự án (prompt §2.2)

```yaml
PROJECT_NAME: "Chat với tài liệu (CWD) — MVP bản thử nghiệm chạy local"
TEST_PLAN_ID: "TP-CWD-001"
TEST_PLAN_VERSION: "0.1"
TEST_PLAN_OWNER: "QA Lead (tên: OQ-TP-02)"
TEST_PLAN_APPROVERS: "Product Owner; Engineering Lead"
OUTPUT_LANGUAGE: "Vietnamese"
TEST_PLAN_OUTPUT_PATH: "docs/test/TEST_PLAN.md"
TEST_LEVELS: "unit (U), integration/API (I), system/E2E (E), acceptance (A); chất lượng AI (Q), hiệu năng (P), bảo mật (S)"
ENVIRONMENTS: "local Docker Compose — hồ sơ FAKE và REAL; staging AWS: chưa có (OQ-TP-05)"
TEST_DATA_STRATEGY: "synthetic — PDF sinh bằng code, corpus tự soạn; không dùng tài liệu thật của công ty"
ENTRY_CRITERIA: "xem §6.3 và §7.2"
EXIT_CRITERIA: "xem §7.3 — 100% AC P0 đạt, 0 Critical/High mở, các ngưỡng G-06..G-09 và NFR đạt"
COVERAGE_TARGET: "AC 100% có ≥ 1 TC; độ phủ dòng domain/application ≥ 80% (DoD); 100% endpoint trong openapi.json"
RISK_TIER: "High"
REGULATORY_CONTEXT: "Quy định bảo vệ dữ liệu cá nhân Việt Nam + NDA với đối tác (CON-006); BRU-001..007"
```

**Lý do RISK_TIER = High:** hai động lực kiến trúc ưu tiên cao nhất là bảo mật dữ liệu (RSK-002) và độ đúng của câu trả lời AI (RSK-001) [Source: docs/design/SAD.md §1.1]; G-10 là điều kiện chặn tuyệt đối [Source: docs/requirements/PRD.md §5.1 D].

### 0.2 Lịch sử phiên bản

| Phiên bản | Ngày | Thay đổi |
|---|---|---|
| 0.1 | 2026-11-02 | Bản đầu tiên. Mở rộng [02-test-plan.md](02-test-plan.md) (chỉ US-001 + US-009) thành Master Test Plan cho cả 22 story, NFR và launch gate |

---

## 0A. Phân tích tài liệu đầu vào (prompt §7.1)

### 0A.1 Danh mục đầu vào

| ID | Loại | Tài liệu | Phiên bản | Nguồn | Thông tin chính dùng cho kế hoạch | Trạng thái |
|---|---|---|---|---|---|---|
| IN-1 | PRD | [PRD.md](../requirements/PRD.md) (PRD-CWD-001) | 0.4 (2026-10-21) | Product Manager | US + AC (§3), trường hợp biên E-01..E-22 (§4.2), launch gate G-01..G-18, NFR-001..014 (§5.1), truy vết (§7) | Có |
| IN-2 | User Stories | [UserStories.md](../requirements/UserStories.md) (USB-CWD-001) | 0.1 (2026-10-21) | Product Owner | 22 story, AC của US-021/022 (mới), DoR/DoD | Có |
| IN-3 | SAD (IEEE 1016) | [SAD.md](../design/SAD.md) (SAD-CWD-001) | 0.2 (2026-10-21) | Kiến trúc sư | Module, pipeline RAG, QAS-1..6, trạng thái Turn/phiên, bảo mật §4.1, độ tin cậy §4.2, TR-01..05 | Có |
| IN-4 | API / Data | [openapi.json](../design/openapi.json), [schema.sql](../design/schema.sql), [Blueprint_SDD.md](../design/Blueprint_SDD.md) | 1.0.0-draft | Development | 25 endpoint, mã lỗi RFC 9457, ALG-02/03/05 | Có |
| IN-4b | UI/UX | [UI_UX_design/](../design/UI_UX_design/index.html) — 11 màn hình HTML + ảnh | — | Designer | Trạng thái màn hình 01..11 | Có |
| IN-5 | Kế hoạch | [Implementation_Plan.md](../plan/Implementation_Plan.md) (IMP-CWD-001), [tasks/](../implements/tasks/README.md) | 0.2 (2026-10-21) | Development | **Khác biệt bản thử nghiệm so với SAD (§2)**, lộ trình 3 tuần, T-15 | Có |
| IN-6 | Risk tier, nghĩa vụ pháp lý | PRD §5.1 D, §6.4 (CON-006, BRU-001..007), SAD §1.1 | — | — | Xác định RISK_TIER = High; G-10..G-15 | Có |
| IN-7 | Tài liệu test có sẵn | [00-boi-canh-day5.md](00-boi-canh-day5.md), [01](01-pham-vi-va-ac.md), [02](02-test-plan.md), [03](03-ma-tran-ac-tc.md), [test-cases.yaml](test-cases.yaml) | 2026-10-28 | QA | Môi trường, tài khoản, dữ liệu, 10 AC đã viết lại cho đo được, TC-001..035 | Có |

**Thiếu / chưa baseline:**
- PRD v0.4 và UserStories v0.1 đều ở trạng thái Draft/In review — kế hoạch baseline theo hai bản này; thay đổi AC sau đó phải cập nhật Phụ lục A.
- US-021, US-022 chưa có trong PRD (USB-01) — kế hoạch dùng AC trong UserStories.md (ASM-TP-03).
- Bộ câu hỏi kiểm thử 50 câu (G-05, PDEP-05) chưa có; hiện có 20 câu ở `eval/questions.yaml` (OQ-TP-03).
- Không có Software Development Plan/WBS riêng; lịch dựa vào IMP-CWD-001 và mốc PRD.

### 0A.2 Yêu cầu trích từ PRD (tóm tắt — danh sách đầy đủ ở Phụ lục A)

| Nhóm | ID | Số lượng | Ưu tiên |
|---|---|---|---|
| User story | US-001..US-022 | 22 (13 P0, 7 P1, 2 P2) | [Source: UserStories.md §2] |
| Tiêu chí chấp nhận | AC-US001-1 .. AC-US022-4 | 49 | |
| NFR | NFR-001..NFR-014 | 14 | [Source: PRD.md §5.1 C–E] |
| Trường hợp biên | E-01..E-22 | 22 | [Source: PRD.md §4.2] |
| Launch gate | G-01..G-18 | 18 | [Source: PRD.md §5.1] |
| Quy tắc nghiệp vụ | BRU-001..BRU-007 | 7 | [Source: PRD.md §7] |

### 0A.3 Phần tử thiết kế (SAD, IEEE 1016) cần kiểm

| Góc nhìn | Phần tử | Loại | Giao diện | Trạng thái | Phụ thuộc |
|---|---|---|---|---|---|
| Composition | `access`, `documents`, `ingestion`, `qa`, `feedback_analytics`, `audit`, `admin` | Module FastAPI | REST `/api/v1` | — | PostgreSQL |
| Component & Connector | `api` (FastAPI), `worker` (poll bảng `documents`), `web` (React SPA) | Deployable | REST, SSE | — | Docker Compose |
| Interaction | Hỏi đáp có căn cứ (SAD §3.2.1); xử lý tài liệu (§3.2.2); gỡ tài liệu (§3.2.3); thu hồi quyền (§3.2.4) | Sequence | SSE `answer.*` | — | Anthropic API, bge-m3 |
| Information | `documents`, `chunks` (1 đoạn = 1 trang), `turns`, `citations`, `audit_log`, `memberships`, `sessions` | Schema | — | — | pgvector, unaccent |
| Interface | 25 endpoint trong openapi.json | REST/SSE | Mã lỗi RFC 9457 | — | — |
| State dynamics | Tài liệu `uploaded → processing → ready / failed`; Turn `completed / stopped / incomplete`; phiên `active / expired / revoked` | State machine | — | SAD §3.1, §3.3 | — |
| Algorithm | ALG-02 chia đoạn theo trang; ALG-03 RRF; ngưỡng τ; ALG-05 `CitationFilter` | Thuật toán | — | — | — |

### 0A.4 Phần tử UI/UX

| Màn hình | Trạng thái cần kiểm | Story |
|---|---|---|
| 01 Đăng nhập | mặc định, phiên hết hạn, lỗi | US-012 |
| 02 Trạng thái trống | chưa có tài liệu, đang xử lý | US-003, 005, 006 (E-01, E-02) |
| 03 Xác nhận phân loại | ô tích, nút bị vô hiệu | US-001 |
| 04 Tải lên & xử lý | thành viên, trưởng nhóm, lỗi từng file | US-001..005 |
| 05 Hỏi đáp | streaming, hoàn tất, đánh giá, đã sao chép | US-006..011, 015..018 |
| 06 Trích dẫn | đoạn trích, tài liệu đã gỡ | US-009, 019, 020 |
| 07 Trạng thái câu trả lời | không tìm thấy, làm rõ, đã dừng, gián đoạn, giới hạn | US-007, 008, 010, 017 |
| 08–10 Quản trị | nhóm truy cập, gỡ tài liệu, nhật ký | US-020..022 |
| 11 Không có quyền | chưa thuộc nhóm, bị thu hồi | US-013, 014 |

[Source: UserStories.md §4.1]

### 0A.5 Phần tử API (trích openapi.json)

| Endpoint | Method | Lỗi cần kiểm | Cần đăng nhập |
|---|---|---|---|
| `/auth/login`, `/auth/callback` | GET | 400 | Không |
| `/auth/logout`, `/me` | POST, GET | 401 | Có |
| `/doc-sets/{dsid}/documents` | GET, POST | 401, 403, 409 `CLASSIFICATION_REQUIRED`/`DOC_SET_FULL`, 413, 415 | Có |
| `/doc-sets/{dsid}/documents:batch` | POST | 207, 403 | Có (Quản lý) |
| `/doc-sets/{dsid}/documents/events` | GET (SSE) | 401, 403 | Có |
| `/doc-sets/{dsid}/classification-confirmations` | POST | 401, 403 | Có |
| `/documents/{docId}/file` | GET | 403, 410 `DOCUMENT_REMOVED` | Có |
| `/doc-sets/{dsid}/conversations` | POST | 401, 403 | Có |
| `/conversations/{cid}/messages` | POST (SSE) | 409 `NO_READY_DOCUMENTS`, 422, 429 | Có |
| `/messages/{mid}:stop` | POST | 403, 404 | Có (chủ hội thoại) |
| `/citations/{citId}` | GET | 403, 404, 410 | Có |
| `/messages/{mid}/feedback` | PUT | 403, 404, 422 | Có |
| `/events` | POST | 422 | Có |
| `/admin/doc-sets/{dsid}/members[/{uid}]` | GET, POST, PATCH, DELETE | 403, 404 `USER_NOT_IN_DIRECTORY`, 409 | Có (Quản trị viên) |
| `/admin/doc-sets/{dsid}/documents`, `/admin/documents/{docId}` | GET, DELETE | 403, 404 | Có (Quản trị viên) |
| `/admin/audit-logs`, `/admin/audit-logs:export` | GET | 403, 422 | Có (Quản trị viên) |
| `/healthz`, `/readyz` | GET | 503 | Không |

### 0A.6 User story và AC

Toàn bộ 22 story, 49 AC và TC tương ứng: **Phụ lục A**. Với US-001 và US-009, kế hoạch dùng bản AC đã viết lại cho đo được (AC-US001-1a/1b, AC-US009-3a/3b) [Source: 01-pham-vi-va-ac.md §2]; bản sửa chờ PO duyệt (OI-T2).

### 0A.7 Đánh giá rủi ro

Xem §15 và **Phụ lục B**.

---

## 1.0 Test Plan Identifier (IEEE 829 §5.1)

| Thuộc tính | Giá trị |
|---|---|
| Document ID | TP-CWD-001 |
| Document Version | 0.1 |
| Issue Date | 2026-11-02 |
| Status | Draft |
| Classification | Nội bộ |
| Prepared By | QA Lead (bản nháp do Claude soạn hỗ trợ) |
| Approved By | Product Owner; Engineering Lead — chưa ký (§16) |

---

## 2.0 Introduction (IEEE 829 §5.2)

### 2.1 Mục đích

Master Test Plan này:
- xác định chiến lược kiểm thử cho **bản thử nghiệm chạy local** của "Chat với tài liệu" [Source: Implementation_Plan.md §1];
- liệt kê các mức, loại và chu kỳ kiểm thử;
- phân vai, trách nhiệm và lịch;
- đặt tiêu chí vào/ra cho từng mức, tiêu chí tạm dừng/tiếp tục;
- nêu môi trường, công cụ, dữ liệu cần có;
- cung cấp truy vết yêu cầu → test case (Phụ lục A), là phần còn trống `[TBD: QA]` ở PRD §7.

**Sản phẩm:** ứng dụng web để đội BD tải PDF dự án lên, hỏi bằng tiếng Việt hoặc tiếng Anh, nhận câu trả lời streaming **chỉ dựa trên tài liệu**, mỗi thông tin có **trích dẫn tên file và số trang**; quản trị viên quản lý thành viên, gỡ tài liệu, xem nhật ký nhưng không thấy nội dung (BRU-007).

### 2.2 Phạm vi

**Trong phạm vi:**
- Chức năng của 22 user story (EP-01..EP-04) theo 49 AC.
- Trường hợp biên E-01..E-22, trừ những mục ở §5.
- API: mọi endpoint trong openapi.json đã có trong bản build (hợp đồng + lỗi).
- UI: 11 màn hình, trạng thái theo §0A.4.
- Chất lượng câu trả lời AI: G-06..G-09 trên bộ câu hỏi kiểm thử, với Claude thật.
- Hiệu năng: NFR-001..NFR-007 trên máy tham chiếu local.
- Bảo mật: phân quyền G-11, không log nội dung G-13, quét phụ thuộc G-15, XSS từ nội dung tài liệu.
- Khả năng tiếp cận: bàn phím và axe-core (DoD, PCON-02 — mục tiêu P1).
- Hồi quy cho mọi thay đổi.
- Nghiệm thu: PO trên môi trường local; người chấm BD cho các AC đo bằng bộ câu hỏi.

**Ngoài phạm vi:** xem §5 (kèm lý do và kế hoạch sau).

### 2.3 Mục tiêu

| ID | Mục tiêu | Tiêu chí thành công | Truy vết |
|---|---|---|---|
| OBJ-001 | Xác nhận yêu cầu chức năng | 100% AC của story P0 đạt (G-01); AC P1/P2 đạt hoặc có quyết định PO | US-001..US-022 |
| OBJ-002 | Xác nhận hợp đồng API | 100% endpoint của bản build có test hợp đồng; mọi sai khác với openapi.json được ghi nhận và quyết định (OQ-TP-04) | openapi.json |
| OBJ-003 | Xác nhận UI khớp thiết kế | 11/11 màn hình, mọi trạng thái ở §0A.4 có ít nhất 1 kiểm tra E2E hoặc thủ công | UI_UX_design |
| OBJ-004 | Khả năng tiếp cận | axe-core 0 lỗi mức serious/critical; dùng được bằng bàn phím | DoD, PCON-02 |
| OBJ-005 | Hiệu năng | NFR-001 p90 ≤ 5 s; NFR-002 p90 ≤ 20 s; NFR-003 ≤ 2 phút/50 trang, ≤ 8 phút/200 trang | NFR-001..007 |
| OBJ-006 | Bảo mật | G-11 100% đạt; G-13 0 nội dung trong log/nhật ký; G-15 0 lỗ hổng Critical/High | G-11, G-13, G-15 |
| OBJ-007 | Chất lượng AI | G-06 ≥ 80% mỗi ngôn ngữ; G-07 ≥ 70%; G-08 ≥ 90%; G-09 100% | AC-US006-2, 007-1, 008-1, 009-3, 010-1 |

### 2.4 Tài liệu tham chiếu

| Tài liệu | Phiên bản | Nguồn |
|---|---|---|
| BRD-CWD-001 [BRD.md](../requirements/BRD.md) | 0.4 | BA |
| PRD-CWD-001 [PRD.md](../requirements/PRD.md) | 0.4 | Product Manager |
| USB-CWD-001 [UserStories.md](../requirements/UserStories.md) | 0.1 | Product Owner |
| [UseCase_Specification.md](../requirements/UseCase_Specification.md) | 0.2 | BA |
| SAD-CWD-001 [SAD.md](../design/SAD.md) | 0.2 | Kiến trúc sư |
| [Blueprint_SDD.md](../design/Blueprint_SDD.md) | 0.2 | Kiến trúc sư |
| [openapi.json](../design/openapi.json) | 1.0.0-draft | Development |
| [UI_UX_design](../design/UI_UX_design/index.html) | — | Designer |
| IMP-CWD-001 [Implementation_Plan.md](../plan/Implementation_Plan.md) | 0.2 | Development |
| IEEE 829-2008 | 2008 | IEEE |

---

## 3.0 Test Items (IEEE 829 §5.3)

### 3.1 Phần mềm được kiểm thử

| Item ID | Tên | Phiên bản | Vị trí | Ghi chú |
|---|---|---|---|---|
| SI-001 | Backend API (FastAPI, Python 3.12) | commit `20031fe` | `backend/app/` | Module `auth`, `documents`, `qa`, `admin`, `audit` |
| SI-002 | Worker xử lý tài liệu | `20031fe` | `backend/app/ingestion/` | pypdf, chia đoạn theo trang, embedding `bge-m3` (hoặc giả) |
| SI-003 | Web SPA (React 18 + TypeScript + Vite) | `20031fe` | `web/src/` | |
| SI-004 | Lược đồ CSDL (PostgreSQL 16 + pgvector + unaccent) | Alembic head tại `20031fe` | `backend/alembic/`, `docs/design/schema.sql` | |
| SI-005 | Cấu hình | `20031fe` | `.env.example`, `docker-compose.yml`, `backend/app/config.py` | Biến `LLM_FAKE`, `EMBED_FAKE`, `RETRIEVAL_NOT_FOUND_TAU`, `LLM_MODEL` |
| SI-006 | Dữ liệu mẫu | `20031fe` | `backend/app/seed.py` | 5 tài khoản, bộ "Dự án X" |
| SI-007 | Tài liệu API | 1.0.0-draft | `docs/design/openapi.json` | Dùng làm oracle cho test hợp đồng |

**Khác biệt của test item so với thiết kế gốc** [Source: Implementation_Plan.md §2]: chạy Docker Compose local thay AWS; Claude qua Anthropic API thay Bedrock; `bge-m3` local thay Cohere; đăng nhập giả lập thay Microsoft 365; danh sách tài liệu poll 3 s thay SSE; không có CI/CD, giám sát, analytics, giới hạn chi phí, dọn dữ liệu, xuất CSV. Các phần này quyết định mục §5.

### 3.2 Test artifact

| ID | Artifact | Định dạng | Vị trí | Bên cung cấp |
|---|---|---|---|---|
| TA-001 | Định nghĩa PASS/FAIL máy đọc | YAML | `docs/test/test-cases.yaml` (TC-001..035; mở rộng TC-036+ theo Phụ lục A) | QA |
| TA-002 | Test unit/integration backend | pytest | `backend/tests/**` | Dev + QA |
| TA-003 | Test unit frontend | Vitest | `web/src/**/*.test.ts(x)` | Dev |
| TA-004 | Test E2E | Playwright | `web/e2e/*.spec.ts` | QA |
| TA-005 | Bộ đánh giá chất lượng AI | Python + YAML | `eval/run_eval.py`, `eval/check_grounding.py`, `eval/questions.yaml`, `eval/corpus_src.json` | QA + Trưởng nhóm BD |
| TA-006 | Đo hiệu năng | Python | `eval/measure_ingest.py`; `eval/load_qa.py` *(cần viết, TK-12)* | QA |
| TA-007 | Mô phỏng | Python | `FakeLlmClient`, embedding giả (`LLM_FAKE=1`, `EMBED_FAKE=1`) | Dev |
| TA-008 | Dữ liệu PDF | sinh bằng code | `backend/tests/pdf_factory.py`, `web/e2e/fixtures/pdf.ts` | QA |

---

## 4.0 Features to be Tested (IEEE 829 §5.4)

### 4.1 Ma trận ưu tiên

Điểm rủi ro = Khả năng × Ảnh hưởng (thang 1–5, tối đa 25), lấy từ Phụ lục B.

| Ưu tiên | Tính năng | Story | Yêu cầu | Điểm rủi ro |
|---|---|---|---|---|
| **Cao** | F-02 Trích dẫn đúng file/trang, loại thông tin không nguồn | US-009 | BR-008, BRU-006, G-09 | 20 |
| **Cao** | F-05 Phân quyền và tách quyền quản trị | US-012, 013, 014, 021 | BR-013, BR-015, BRU-007, G-11 | 20 |
| **Cao** | F-03 Trả lời chỉ từ tài liệu, "không tìm thấy" | US-007, 010 | BR-006, BR-009, G-08 | 16 |
| **Cao** | F-06 Gỡ hoàn toàn tài liệu | US-020 | BR-017 | 15 |
| **Cao** | F-01 Tải lên và xử lý PDF | US-001, 002, 004, 005 | BR-001, BR-002, BRU-001, NFR-003 | 12 |
| **Trung bình** | F-04 Hỏi đáp tự nhiên, đa tài liệu, tiếp nối | US-006, 008, 011 | BR-005, 007, 010, NFR-001/002/004 | 12 |
| **Trung bình** | F-07 Nhật ký truy cập | US-022 | BR-016, NFR-010, G-13 | 10 |
| **Thấp** | F-08 Điều khiển câu trả lời (Dừng, Sao chép, Hội thoại mới, Mở PDF) | US-016, 017, 018, 019 | BR-005, BR-008, BR-010 | 6 |
| **Thấp** | F-09 Đánh giá câu trả lời | US-015 | BR-014 | 4 |
| **Thấp** | F-10 Danh sách tài liệu | US-003 | BR-003 | 4 |

### 4.2 Ma trận tính năng × loại kiểm thử

| Tính năng | U | I | E | A | Hồi quy | P | S | A11y | Q (AI) |
|---|---|---|---|---|---|---|---|---|---|
| F-01 Tải lên & xử lý | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (magic bytes, kích thước) | ✓ | — |
| F-02 Trích dẫn | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ (XSS) | ✓ | ✓ |
| F-03 Chỉ từ tài liệu | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — | ✓ |
| F-04 Hỏi đáp | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| F-05 Phân quyền | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| F-06 Gỡ tài liệu | — | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| F-07 Nhật ký | — | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |
| F-08 Điều khiển câu trả lời | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (Dừng ≤ 1 s) | — | ✓ | — |
| F-09 Đánh giá | — | ✓ | ✓ | ✓ | ✓ | — | — | ✓ | — |
| F-10 Danh sách | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — |

### 4.3 Mô tả tính năng

| Feature ID | Tính năng | Phần kiểm được | AC |
|---|---|---|---|
| F-01 | Tải lên và xử lý PDF | Xác nhận phân loại 1 lần/phiên; tải 1 file; tải lô (chỉ Quản lý); từ chối không phải PDF, quá 20 MiB, quá 200 trang, hỏng, mật khẩu, scan; tiến trình %; trùng tên; đầy 50 file | AC-US001-1a..4, AC-US002-1..4, AC-US004-1, AC-US005-1 |
| F-02 | Trích dẫn | `[n]` có tên file + trang; popover ≤ 300 ký tự; đoạn trích nằm trên trang; loại khối không nguồn | AC-US009-1..4 |
| F-03 | Chỉ từ tài liệu | Ngưỡng τ, marker `[KHONG_TIM_THAY]`, kiến thức ngoài, gợi ý hành động | AC-US007-1/2, AC-US010-1/2 |
| F-04 | Hỏi đáp | Gửi bằng Enter, ô rỗng, ≤ 2000 ký tự, đa tài liệu, mâu thuẫn, tiếp nối, song ngữ | AC-US006-1..3, AC-US008-1/2, AC-US011-1/2 |
| F-05 | Phân quyền | Chưa đăng nhập, hết phiên giữ bản nháp, người ngoài nhóm, admin chỉ thấy mô tả, thu hồi quyền, thêm/gỡ/đổi vai trò | AC-US012-1/2, AC-US013-1/2, AC-US014-1/2, AC-US021-1..5 |
| F-06 | Gỡ tài liệu | Xóa file, đoạn, trích dẫn; biến khỏi danh sách ≤ 10 s; câu hỏi sau đó "không tìm thấy"; chỉ admin | AC-US020-1/2 |
| F-07 | Nhật ký | Lọc theo bộ/khoảng thời gian/người/thao tác; không nội dung; > 12 tháng; xuất CSV | AC-US022-1..4 |
| F-08 | Điều khiển câu trả lời | Dừng ≤ 1 s; sao chép kèm nguồn; hội thoại mới; mở PDF đúng trang | AC-US016-1, AC-US017-1, AC-US018-1, AC-US019-1 |
| F-09 | Đánh giá | 👍/👎 + lý do; thay đánh giá | AC-US015-1/2 |
| F-10 | Danh sách | Tên, số trang, trạng thái, mới nhất trước | AC-US003-1 |

---

## 5.0 Features Not to be Tested (IEEE 829 §5.5)

| ID | Tính năng / yêu cầu | Lý do | Rủi ro | Kế hoạch sau | Owner |
|---|---|---|---|---|---|
| NT-01 | NFR-012 độ sẵn sàng ≥ 95% giờ làm việc | Cần môi trường vận hành + canary (SAD §4.3); test item chạy local | Trung bình | Đo trên staging trong 4 tuần thử nghiệm | Trưởng phòng CNTT (OQ-TP-05) |
| NT-02 | NFR-013 RTO/RPO, diễn tập khôi phục (G-18 phần khôi phục) | Không có RDS/PITR ở local | Trung bình | Diễn tập trên staging trước 2027-01-04 | Trưởng phòng CNTT |
| NT-03 | G-12 TLS ≥ 1.2 và mã hóa khi lưu | Local chạy HTTP, đĩa không mã hóa | Cao | Kiểm cấu hình trên staging (testssl, kiểm KMS) | Trưởng phòng CNTT |
| NT-04 | G-14 tự động xóa theo BRU-002..004; AC-US022-3 phần "lưu 12 tháng" | Job `retention` không có trong test item (IMP §2) | Trung bình | Kiểm khi job được làm | Engineering Lead |
| NT-05 | G-16, E-13 giới hạn 30 câu/giờ và trần chi phí | `billing_guard` không có trong test item (IMP §2) | Trung bình | Kiểm khi làm; trước pilot cần quyết định PO (OQ-TP-07) | Product Owner |
| NT-06 | AC-US022-4 xuất CSV (P1) | Không có trong test item (IMP §2). TC-081 đã viết sẵn, ở trạng thái **Deferred** | Thấp | Chạy TC-081 khi tính năng có | Product Owner (OQ-TP-06) |
| NT-07 | Đăng nhập Microsoft 365 thật (IF-02), tra tài khoản qua Graph | Thay bằng đăng nhập giả lập; AC-US021-2 kiểm với danh bạ giả lập (ASM-TP-02) | Trung bình | Kiểm OIDC + Graph trên staging | Trưởng phòng CNTT (PDEP-03) |
| NT-08 | E-21, COM-04 chặn ngoài VPN | Do hạ tầng mạng | Thấp | Kiểm cấu hình mạng khi triển khai | Trưởng phòng CNTT |
| NT-09 | Analytics EVT-001..016, Metabase | Không có trong test item (IMP §2) | Thấp | Kiểm khi làm; ràng buộc G-13 vẫn kiểm ở log ứng dụng | Product Owner |
| NT-10 | NFR-008 mở rộng gấp 5 lần | Là đánh giá thiết kế, không phải kiểm thử | Thấp | Review SAD §4.4 | Engineering Lead |
| NT-11 | G-10 phê duyệt pháp lý BRU-005 | Review hợp đồng, không phải kiểm thử phần mềm | Cao (chặn ra mắt) | Theo PDEP-01 | Pháp chế + CNTT |
| NT-12 | Penetration test, quét image (Amazon Inspector), WAF | Ngoài phạm vi bản local; không có hạ tầng | Trung bình | Đội bảo mật CNTT trên staging | Trưởng phòng CNTT |
| NT-13 | Trình duyệt ngoài Chrome/Edge, thiết bị di động, màn < 768 px | Ngoài G-04 và §6.1 PRD | Thấp | — | — |
| NT-14 | SSE trạng thái tài liệu `/documents/events` | Bản thử nghiệm thay bằng poll 3 s (IMP §2); yêu cầu "≤ 5 s" vẫn kiểm qua TC-045/046 | Thấp | Kiểm khi chuyển sang SSE | Engineering Lead |
| NT-15 | ClamAV quét mã độc (SAD §4.1, P1) | Không có trong test item | Thấp | — | Engineering Lead |

Các test hiện có của những phần trên (nếu có) **vẫn chạy như hồi quy** nhưng không tính vào verdict của kế hoạch này.

---

## 6.0 Approach (IEEE 829 §5.6)

### 6.1 Mức và loại kiểm thử

Thứ tự chạy: **U → I → E → Q → P**. Lớp dưới đỏ thì không chạy lớp trên [Source: 02-test-plan.md].

#### 6.1.1 Unit (U)

| Thuộc tính | Mô tả |
|---|---|
| Người chịu trách nhiệm | Developer (viết), QA (review assert đối chiếu `expect`) |
| Công cụ | pytest (backend), Vitest + Testing Library (frontend) |
| Mục tiêu độ phủ | ≥ 80% dòng cho `backend/app` phần nghiệp vụ (DoD); 100% nhánh của `CitationFilter`, `policy.py`, `chunker.py` |
| Tiêu chí vào | Code đã review; `ruff check .` sạch |
| Tiêu chí ra | 100% test xanh; độ phủ đạt |
| Trọng tâm | `CitationFilter` (ALG-05), RRF và τ (ALG-03), chia đoạn theo trang (ALG-02), bảng chân trị `AccessPolicy`, component hiển thị `[n]`/popover/ghi chú, hộp xác nhận, retry tải lên |
| Mock | `FakeLlmClient` có kịch bản; embedding giả; không gọi mạng |

#### 6.1.2 Integration / API (I)

| Thuộc tính | Mô tả |
|---|---|
| Người chịu trách nhiệm | Developer + QA |
| Công cụ | pytest + httpx `AsyncClient` + DB `cwd_test`; hồ sơ FAKE |
| Phạm vi | Mọi endpoint của SI-001, worker (SI-002), CSDL (SI-004) |
| Tiêu chí vào | U xanh; migration `alembic upgrade head` chạy được trên `cwd_test` |
| Tiêu chí ra | 100% test xanh; mọi mã lỗi trong §0A.5 có ít nhất 1 test |
| Trọng tâm | Thứ tự sự kiện SSE; bất biến trích dẫn; `pending_documents`; 401/403/409/410/413/415/422; thu hồi quyền ở request kế tiếp; gỡ tài liệu xuyên mọi bảng; nhật ký không nội dung |

**Ca API tiêu biểu:**

| TC | Endpoint | Loại | Kiểm | Kết quả mong đợi |
|---|---|---|---|---|
| TC-001 | `POST /doc-sets/{dsid}/documents` | Dương | 202, `status=uploaded`, `error_code=null` | Tài liệu được nhận |
| TC-016 | `POST /doc-sets/{dsid}/documents` | Âm | Chưa xác nhận phân loại | 409 `CLASSIFICATION_REQUIRED`, 0 dòng `documents` mới |
| TC-043 | `POST /doc-sets/{dsid}/documents` | Âm | File `.docx` (magic `PK`) | 415 `NOT_PDF`, không tạo dòng |
| TC-040 | `POST …/documents` nhiều file | Âm | Thành viên tải lô | 403, không tạo dòng |
| TC-019 | `POST /conversations/{cid}/messages` | Dương | Thứ tự `answer.started → answer.delta* → answer.completed` | `answer_type=answered`, ≥ 1 citation |
| TC-011 | `POST /conversations/{cid}/messages` | Biên | Có tài liệu `processing` | `pending_documents` đúng tập tên |
| TC-068 | `POST /conversations/{cid}/messages` | Âm | Người ngoài nhóm / admin | 403, không có `answer.delta` |
| TC-024 | `GET /citations/{id}` | Dương | Snippet 1–300 ký tự, khớp sự kiện SSE | 200 |
| TC-070 | `DELETE /admin/documents/{id}` → `GET /citations/{id}` | Âm | Sau khi gỡ | 410 `DOCUMENT_REMOVED`; 0 dòng `chunks`; file bị xóa |
| TC-074 | `POST /admin/doc-sets/{dsid}/members` | Âm | Email không có trong danh bạ | 404 `USER_NOT_IN_DIRECTORY`; nhóm không đổi |

#### 6.1.3 System / E2E (E)

| Thuộc tính | Mô tả |
|---|---|
| Người chịu trách nhiệm | QA |
| Công cụ | Playwright, Chromium (Desktop Chrome, 1440×900); thêm project `msedge` cho G-04 (TC-097) |
| Phạm vi | Hành trình người dùng của 3 persona trên 3 tiến trình api + worker + web |
| Tiêu chí vào | I xanh; `docker compose up` khỏe; hồ sơ FAKE; mỗi spec tự `seed --reset` |
| Tiêu chí ra | Mọi spec PASS **3/3 lần chạy liên tiếp** (`--repeat-each=3`); không chấp nhận "chạy lại cho xanh" |
| Trọng tâm | Thấy "Sẵn sàng" không tải lại trang; `Nguồn n`; popover; ghi chú tài liệu chưa sẵn sàng; trang không có quyền; quản trị |

**Hành trình E2E:**

| TC | Hành trình | Bước | Kết quả mong đợi |
|---|---|---|---|
| TC-004 | Lan tải PDF đầu tiên | Đăng nhập → xác nhận phân loại → chọn PDF → chờ | Dòng tài liệu chuyển "Sẵn sàng" không tải lại trang |
| TC-009 | Hỏi về file vừa tải | Bộ có ≥ 2 file → hỏi về nội dung chỉ có ở file F | Có `Nguồn n: F trang p` |
| TC-062 | Mở trích dẫn và PDF gốc | Bấm `[1]` → popover → "Mở tài liệu gốc" | Tab mới, URL có `#page=N` |
| TC-037 | Minh tải lô | Chọn 3 PDF một lần | 3 dòng trạng thái riêng → đều "Sẵn sàng" |
| TC-069 | Anh bị gỡ quyền | Hùng gỡ Anh → Anh thao tác tiếp | Trang "Không có quyền" |
| TC-071 | Hùng gỡ tài liệu | Hùng gỡ X khi Lan đang mở danh sách | X biến khỏi danh sách của Lan ≤ 10 s; trích dẫn cũ báo "đã gỡ" |

#### 6.1.4 Acceptance (A)

| Thuộc tính | Mô tả |
|---|---|
| Người chịu trách nhiệm | Product Owner (nghiệm thu); 2 thành viên BD chấm bộ câu hỏi (PDEP-06); QA điều phối |
| Công cụ | Chạy tay theo [demo-script.md](../implements/demo-script.md) trên local; CSV chấm điểm từ `check_grounding.py --export-review` |
| Phạm vi | 49 AC (Phụ lục A); AC đo bằng bộ câu hỏi chấm theo rubric |
| Tiêu chí vào | U, I, E, Q đã chạy và có báo cáo; không còn lỗi Critical mở |
| Tiêu chí ra | PO ký nhận từng story P0; người chấm hoàn tất CSV |
| Trọng tâm | Giá trị nghiệp vụ, câu chữ thông báo theo PRD §4.2 |

#### 6.1.5 Hồi quy

| Bộ | Phạm vi | Lệnh | Tần suất |
|---|---|---|---|
| REG-001 | Toàn bộ unit + integration backend | `docker compose exec api pytest` | Mỗi thay đổi code |
| REG-002 | Unit frontend | `docker compose exec web npm test` | Mỗi thay đổi code |
| REG-003 | E2E (mọi spec, FAKE) | `cd web && npm run e2e` | Mỗi lần merge; trước mỗi báo cáo |
| REG-004 | Bộ đánh giá AI (REAL) | `run_eval.py` + `check_grounding.py` | Khi đổi prompt, τ, top-k, model hoặc cách chia đoạn (SAD §4.3) |

Khi có CI (hiện chưa có — IMP §2), REG-001..003 chạy trên mỗi pull request.

#### 6.1.6 Hiệu năng (P)

| Thuộc tính | Mô tả |
|---|---|
| Người chịu trách nhiệm | QA (chạy), Engineering Lead (phân tích) |
| Công cụ | `eval/measure_ingest.py` (NFR-003); `run_eval.py` (độ trễ); `eval/load_qa.py` *(cần viết: httpx async, N người dùng ảo, gom `latency_first_token_ms`, `latency_total_ms`)* |
| Hồ sơ | REAL (`LLM_FAKE=0`, `EMBED_FAKE=0`), máy tham chiếu ghi trong báo cáo (OI-T3) |
| Tiêu chí vào | I và E xanh; corpus đã sinh; máy tham chiếu đã chốt |
| Tiêu chí ra | Mọi PERF đạt ngưỡng; ghi p50/p90/max, số mẫu, cấu hình máy, model, τ |

| TC | Yêu cầu | Loại | Tải | Số đo | Ngưỡng |
|---|---|---|---|---|---|
| PERF-001 | NFR-001 | Độ trễ đơn người dùng | 1 người, toàn bộ bộ câu hỏi (≥ 20 câu) | p90 thời gian tới `answer.delta` đầu tiên, đo ở client | ≤ 5 s |
| PERF-002 | NFR-002 | Độ trễ đơn người dùng | như trên | p90 thời gian tới `answer.completed` | ≤ 20 s |
| PERF-003 | NFR-005 | Tải đồng thời | 10 người dùng ảo, mỗi người 5 câu, gửi đồng thời | p90 như PERF-001/002 | ≤ 5 s / ≤ 20 s; 0 lỗi 5xx |
| PERF-004 | NFR-006 | Thông lượng | 20 câu/phút trong 10 phút (10 người × 2 câu/phút; < 30 câu/người/giờ) | p90 + tỷ lệ lỗi | ≤ 5 s / ≤ 20 s; lỗi = 0 |
| PERF-005 | NFR-007 | Dung lượng | Bộ 50 file, trong đó ≥ 5 file 200 trang; tổng ≤ 1 GB | 100% `ready`; PERF-001 chạy lại trên bộ đầy | 100% ready; p90 ≤ 5 s |
| TC-006 | NFR-003 | Thời gian xử lý | 1 PDF 50 trang, 3 lần | thời gian 202 → `ready` (poll 1 s) | ≤ 120 s, 3/3 lần |
| TC-007 | NFR-003 | Thời gian xử lý | 1 PDF 200 trang, 3 lần | như trên | ≤ 480 s, 3/3 lần |
| TC-060 | AC-US017-1 | Độ trễ thao tác | Bấm "Dừng" khi đang stream | thời gian tới khi văn bản ngừng tăng | ≤ 1 s |

#### 6.1.7 Bảo mật (S)

| Thuộc tính | Mô tả |
|---|---|
| Người chịu trách nhiệm | QA + Engineering Lead |
| Công cụ | pytest (phân quyền), `pip-audit`, `npm audit`, Semgrep (SAST, SAD §4.1), quét log bằng script |
| Tiêu chí vào | I xanh |
| Tiêu chí ra | G-11 100% đạt; 0 Critical/High (G-15); 0 nội dung trong log/nhật ký (G-13) |

| TC | Kiểm | Mô tả | Kết quả mong đợi |
|---|---|---|---|
| TC-066..069, 072, 040 | Phân quyền (G-11) | Bảng chân trị vai trò × thao tác; gọi API trực tiếp, không qua UI | 100% khớp ma trận vai trò PRD §5.1 D |
| TC-067 | Tách quyền BRU-007 (QAS-1) | Admin gọi `GET /citations/{id}`, `/documents/{id}/file`, `POST messages` | 403; không lộ nội dung |
| TC-069 | Thu hồi (QAS-2, NFR-011) | Gỡ thành viên khi phiên đang mở | Request kế tiếp bị từ chối |
| TC-079, TC-094 | Không log nội dung (G-13) | Chạy E2E với câu hỏi chứa chuỗi đánh dấu duy nhất; tìm chuỗi đó trong log `api`, `worker`, bảng `audit_log` | 0 lần xuất hiện |
| TC-095 | XSS từ nội dung tài liệu | U: AnswerCard.test "nội dung `<script>`/`<img onerror>` hiển thị dạng chữ" (đã có). E (cần viết): PDF chứa `<img src=x onerror=…>` và markdown HTML thô; hỏi để nội dung đó vào snippet/câu trả lời | Hiển thị như văn bản; không thực thi script |
| TC-096 | Quét phụ thuộc (G-15) | `pip-audit`, `npm audit --omit=dev`, Semgrep | 0 Critical/High chưa xử lý |
| TC-101 | Phiên | Cookie `HttpOnly`, `SameSite=Strict`; token không lưu dạng rõ (test_token_not_stored_in_plaintext); hết hạn 8 giờ | Đúng thuộc tính; 401 sau hết hạn |
| TC-102 | CSRF / header bảo mật (SAD §2.1) | Request đổi dữ liệu thiếu `X-CSRF-Token`; header CSP, `X-Frame-Options` | Theo SAD: từ chối / header có mặt. Nếu bản build không có → ghi lỗi, PO quyết (OQ-TP-04) |

#### 6.1.8 Khả năng tiếp cận

| Thuộc tính | Mô tả |
|---|---|
| Người chịu trách nhiệm | QA |
| Công cụ | `@axe-core/playwright` *(cần thêm, TK-10)*; kiểm bàn phím trong Playwright |
| Chuẩn | WCAG 2.1 AA — mục tiêu P1 (PCON-02); DoD: axe-core không lỗi serious, dùng được bằng bàn phím |
| Tiêu chí ra | 0 vi phạm `serious`/`critical` trên 11 màn hình |

| TC | Kiểm | Kết quả mong đợi |
|---|---|---|
| TC-098 | axe-core trên 11 màn hình, mọi trạng thái §0A.4 | 0 vi phạm serious/critical |
| TC-099 | Bàn phím: Tab tới `[1]`, Enter mở, Esc đóng và trả focus; hộp xác nhận giữ focus | Đúng (chat.spec, ClassificationDialog.test) |

#### 6.1.9 UI/UX

So khớp với 11 màn hình thiết kế bằng E2E (văn bản, trạng thái) và kiểm tay theo ảnh trong `docs/design/UI_UX_design/screenshots/`. Không làm visual-regression tự động trong đợt này. Câu chữ thông báo lỗi so với cột "Thông điệp" PRD §4.2. Độ rộng 1280 px và 768 px (PRD §6.1) kiểm tay.

#### 6.1.10 Chất lượng câu trả lời AI (Q)

| Thuộc tính | Mô tả |
|---|---|
| Người chịu trách nhiệm | QA (chạy), Trưởng nhóm BD (bộ câu hỏi, PDEP-05), 2 thành viên BD (chấm, PDEP-06) |
| Công cụ | `run_eval.py` (gọi API thật, gom SSE), `check_grounding.py` (AC-US009-3a máy; xuất/chấm CSV 3b) |
| Dữ liệu | `eval/corpus/` (sinh từ `corpus_src.json`); `eval/questions.yaml` — hiện 20 câu (8 SC-01, 4 SC-02, 4 SC-03, 4 SC-04; 15 vi, 5 en); **cần 50 câu theo G-05** (OQ-TP-03) |
| Tiêu chí ra | G-06 ≥ 80% mỗi ngôn ngữ; G-07 ≥ 70%; G-08 ≥ 90%; G-09 100%; AC-US011-2 ≥ 4/5 |

**Quy tắc thống kê:** chạy 1 lượt cho mỗi cấu hình (model, τ, prompt); ngưỡng tính trên toàn bộ câu của loại đó, không lấy câu tốt nhất qua nhiều lượt. Đổi cấu hình thì chạy lại toàn bộ.

### 6.2 Tự động và thủ công

| Phần | Tự động | Thủ công | Lý do |
|---|---|---|---|
| U, I | 100% | — | Xác định, nhanh |
| E (FAKE) | 100% các hành trình trong Phụ lục A | Kiểm tay câu chữ, bố cục 768 px | Câu chữ và bố cục khó assert hết |
| Q | Chạy và chấm máy: so khớp `expected`, `answer_type`, file/trang trích dẫn, đoạn trích có trên trang | Người chấm BD: đúng/sai nội dung (AC-US007-1), "đoạn trích có hỗ trợ câu trả lời" (AC-US009-3b), không mâu thuẫn | Máy không đánh giá được ngữ nghĩa |
| P | 100% (script) | Ghi cấu hình máy | — |
| S | Phân quyền, quét phụ thuộc, quét log | Review CSP/cookie | — |
| A | — | PO theo demo-script | Nghiệm thu là quyết định của con người |

### 6.3 Chiến lược thực thi

1. **Chu kỳ 1 — xương sống (US-001, US-009):** theo [02-test-plan.md](02-test-plan.md); TC-001..035.
2. **Chu kỳ 2 — chức năng còn lại:** TC-036..TC-102 lớp U/I/E (FAKE).
3. **Chu kỳ 3 — REAL:** Q (bộ 50 câu khi có) và P.
4. **Chu kỳ 4 — hồi quy + nghiệm thu:** REG-001..004, PO nghiệm thu, báo cáo tổng kết.

Mỗi TC có verdict `PASS` / `FAIL` / `BLOCKED` theo quy tắc ở đầu `test-cases.yaml`: `BLOCKED` không phải `PASS`; khối `expect` viết trước khi chạy, không sửa sau khi thấy kết quả.

**Phân loại lỗi:** Critical (mất/lộ dữ liệu, vượt quyền, câu trả lời không nguồn được hiển thị, sập luồng chính) · High (AC P0 sai, không có cách vòng) · Medium (AC P1/P2 sai hoặc P0 sai có cách vòng) · Low (câu chữ, giao diện).

---

## 7.0 Item Pass/Fail Criteria (IEEE 829 §5.7)

### 7.1 Mức test case

PASS ⇔ lệnh chạy kết thúc exit code 0 **và** mọi mệnh đề `expect` được hiện thực thành assert và đúng. Lớp E: PASS 3/3 lần liên tiếp. Lớp Q/P: số đo đạt ngưỡng trong bảng §6.1.6/§6.1.10.

### 7.2 Tiêu chí vào (toàn kế hoạch)

| # | Tiêu chí | Cách kiểm |
|---|---|---|
| EN-1 | `docker compose up -d` khỏe; `GET /api/v1/health` = 200 | Lệnh |
| EN-2 | `alembic upgrade head` và `python -m app.seed --reset` chạy được | Lệnh |
| EN-3 | `ruff check .` sạch; build web không lỗi kiểu | Lệnh |
| EN-4 | TC ở trạng thái `to-write` đã được viết và review đối chiếu `expect` trước lần chạy đầu | Review |
| EN-5 | Với Q/P: khóa API Anthropic có ngân sách đã duyệt (OQ-TP-08); corpus đã sinh; máy tham chiếu đã chốt (OI-T3) | Checklist |

### 7.3 Tiêu chí ra (tất cả phải đúng)

| # | Tiêu chí | Ngưỡng | Nguồn |
|---|---|---|---|
| EX-1 | AC của story P0 | 100% PASS | G-01 |
| EX-2 | AC của story P1/P2 | 100% PASS, hoặc PO chấp nhận bằng văn bản từng AC chưa đạt | DoD |
| EX-3 | Trường hợp biên E-01..E-22 trong phạm vi | 100% đã chạy; 0 lỗi Critical/High | G-02 |
| EX-4 | Lỗi tồn đọng | 0 Critical, 0 High; Medium có kế hoạch | G-03 |
| EX-5 | Phân quyền | 100% TC của G-11 PASS | G-11 |
| EX-6 | Chất lượng AI | G-06 ≥ 80% từng ngôn ngữ; G-07 ≥ 70%; G-08 ≥ 90%; G-09 100% | G-06..G-09 |
| EX-7 | Hiệu năng | PERF-001..005, TC-006/007 đạt trên máy tham chiếu | NFR-001..007 |
| EX-8 | Hồi quy | REG-001..003 xanh toàn bộ (không chỉ TC trong phạm vi) | — |
| EX-9 | Độ phủ | Mỗi AC có ≥ 1 TC (Phụ lục A); độ phủ dòng nghiệp vụ backend ≥ 80% | DoD |
| EX-10 | Báo cáo | `docs/test/reports/<ngày>.md`: verdict từng TC/AC, commit, hồ sơ, τ, model, máy | — |

Một TC `FAIL` hoặc `BLOCKED` ⇒ AC tương ứng `FAIL`. AC có TC Deferred (NT-06) không tính vào EX-1/EX-2 khi PO đã chấp nhận hoãn.

---

## 8.0 Suspension and Resumption Criteria (IEEE 829 §5.8)

### 8.1 Tạm dừng

| # | Điều kiện | Phạm vi tạm dừng |
|---|---|---|
| SU-1 | `docker compose up` hoặc migration lỗi, hoặc `/health` ≠ 200 quá 15 phút | Toàn bộ |
| SU-2 | REG-001 (pytest) đỏ > 10% số test, hoặc luồng xương sống (TC-001, TC-019) FAIL | Lớp E, Q, P |
| SU-3 | Phát hiện lỗi Critical về bảo mật (lộ nội dung cho người không có quyền, nội dung trong log) | Toàn bộ chu kỳ, báo ngay Engineering Lead + PO |
| SU-4 | Cùng một spec E2E chập chờn ≥ 2 lần trong 3 lần chạy mà không rõ nguyên nhân | Spec đó; không tính PASS |
| SU-5 | Anthropic API lỗi/429 liên tục > 30 phút, hoặc chi phí chạy Q/P vượt ngân sách đã duyệt (OQ-TP-08) | Lớp Q, P |
| SU-6 | Dữ liệu DB bị bẩn do chạy song song (E2E dùng chung DB `cwd`) | Lớp E |

### 8.2 Tiếp tục

| # | Điều kiện | Việc phải làm |
|---|---|---|
| RE-1 | Đã có bản sửa (commit) cho nguyên nhân tạm dừng | Ghi commit vào báo cáo |
| RE-2 | Môi trường dựng lại sạch: `docker compose down -v` → `up -d` → `alembic upgrade head` → `seed --reset` | Kiểm lại EN-1..EN-3 |
| RE-3 | Chạy lại REG-001, REG-002 xanh | Lệnh |
| RE-4 | Chạy lại **toàn bộ** lớp bị tạm dừng (không chỉ TC đã FAIL) | — |
| RE-5 | Với SU-3: Engineering Lead xác nhận bằng văn bản đã đóng lỗ hổng; thêm test hồi quy cho lỗi đó | — |
| RE-6 | Với SU-5: PO duyệt lại ngân sách hoặc API ổn định 30 phút | — |

---

## 9.0 Test Deliverables (IEEE 829 §5.9)

| ID | Sản phẩm | Vị trí | Khi nào |
|---|---|---|---|
| D-01 | Master Test Plan (tài liệu này) | `docs/test/TEST_PLAN.md` | Trước chu kỳ 2 |
| D-02 | Checklist tự kiểm IEEE 829 | `docs/test/Test_Plan_IEEE_829_Checklist.xlsx` | Cùng D-01 |
| D-03 | Định nghĩa test case PASS/FAIL (mở rộng TC-036..102, PERF-001..005) | `docs/test/test-cases.yaml` | Trước khi chạy chu kỳ 2 |
| D-04 | RTM (ma trận AC ↔ TC kèm verdict) | `docs/test/03-ma-tran-ac-tc.md` (mở rộng) | Mỗi chu kỳ |
| D-05 | Mã test | `backend/tests/`, `web/src/**/*.test.*`, `web/e2e/`, `eval/` | Liên tục |
| D-06 | Báo cáo mỗi lượt chạy | `docs/test/reports/<ngày>.md` | Mỗi chu kỳ |
| D-07 | Báo cáo đánh giá AI + CSV chấm | `eval/reports/<ngày>.md`, `<ngày>.json`; CSV chấm (gitignore, không chứa nội dung khi commit) | Chu kỳ 3 |
| D-08 | Báo cáo hiệu năng | `eval/reports/ingest-*.json`, `load-*.json` | Chu kỳ 3 |
| D-09 | Danh sách lỗi | Issue tracker *(chưa chọn — OQ-TP-09)* | Liên tục |
| D-10 | Test Summary Report (tổng kết, đề xuất go/no-go) | `docs/test/reports/summary-<ngày>.md` | Chu kỳ 4 |

---

## 10.0 Testing Tasks (IEEE 829 §5.10)

| ID | Việc | Phụ thuộc | Người làm | Ước lượng |
|---|---|---|---|---|
| TK-01 | Review và phê duyệt TP-CWD-001; trả lời OQ-TP-01..09, OI-T1..T3 | — | QA Lead, PO, Engineering Lead | 0,5 ngày |
| TK-02 | Mở rộng `test-cases.yaml` với TC-036..102, PERF-001..005 (khối `expect` trước khi chạy) | TK-01 | QA | 1,5 ngày |
| TK-03 | Chạy E2E chu kỳ 1 (TC-004, 009, 014, 017, 018, 022, 027) `--repeat-each=3` | Playwright cài trên host | QA | 0,5 ngày |
| TK-04 | Viết TC `to-write` lớp I: TC-036, 070 (5 câu), 080, 089 | TK-02 | Developer + QA | 1,5 ngày |
| TK-05 | Viết TC `to-write` lớp E: TC-042, 046, 060, 065, 071, 084, 092 | TK-02 | QA | 2 ngày |
| TK-06 | Viết TC bảo mật: TC-094, 095, 102; chạy TC-096 | TK-02 | QA + Engineering Lead | 1 ngày |
| TK-07 | Sinh dữ liệu: PDF 50/200 trang chữ dày, PDF đúng 20 971 520 byte, bộ 50 file (PERF-005, TC-039) | — | QA | 0,5 ngày |
| TK-08 | Nhận bộ 50 câu hỏi + đáp án (G-05) và đưa vào `eval/questions.yaml` | PDEP-05 | Trưởng nhóm BD → QA | 0,5 ngày (sau khi nhận) |
| TK-09 | Chạy Q (REAL), xuất CSV, người chấm điền, chấm điểm | TK-08, OQ-TP-08 | QA, 2 thành viên BD | 1 ngày + 1 ngày chấm |
| TK-10 | Thêm axe-core vào Playwright; chạy TC-098; thêm project `msedge` (TC-097) | TK-03 | QA | 1 ngày |
| TK-11 | Đo NFR-003 (TC-006, 007) | OI-T3, TK-07 | QA | 0,5 ngày |
| TK-12 | Viết `eval/load_qa.py`; chạy PERF-001..005 | OI-T3, OQ-TP-08 | QA + Engineering Lead | 1,5 ngày |
| TK-13 | Hồi quy toàn bộ REG-001..004 | Mọi sửa lỗi | QA | 0,5 ngày |
| TK-14 | Nghiệm thu PO theo demo-script | TK-13 | PO, QA | 0,5 ngày |
| TK-15 | Viết Test Summary Report, cập nhật RTM | TK-14 | QA Lead | 0,5 ngày |

---

## 11.0 Environmental Needs (IEEE 829 §5.11)

### 11.1 Hồ sơ môi trường

| Hồ sơ | Biến `.env` | Dùng cho |
|---|---|---|
| FAKE | `LLM_FAKE=1`, `EMBED_FAKE=1`, `RETRIEVAL_NOT_FOUND_TAU=0.25` | U, I, E — miễn phí, xác định |
| REAL | `LLM_FAKE=0`, `EMBED_FAKE=0`, `ANTHROPIC_API_KEY=<bí mật, không commit>`, τ = 0,35, `LLM_MODEL=claude-opus-5-5` | Q, P |

[Source: test-cases.yaml `profiles`; 00-boi-canh-day5.md §2]

### 11.2 Phần cứng và phần mềm

| Hạng mục | Yêu cầu |
|---|---|
| Máy chạy | Windows 10/11 + Docker Desktop (WSL2). Máy tham chiếu cho P: **chưa chốt** CPU/RAM/GPU (OI-T3). `bge-m3` chạy CPU |
| Container | `db` (PostgreSQL 16 + pgvector + unaccent), `api`, `worker`, `web` (Vite dev :5173) |
| Host | Node.js + Playwright Chromium (và Edge cho TC-097); Python 3.12 cho script `eval/` nếu chạy ngoài container |
| CSDL | `cwd` (E/Q/P), `cwd_test` (I). Tạo `cwd_test` nếu thiếu: `psql -c "CREATE DATABASE cwd_test OWNER cwd"` |
| Dịch vụ ngoài | Anthropic API (chỉ REAL); không cần Microsoft 365 (đăng nhập giả lập) |
| URL | Web http://localhost:5173 · API http://localhost:8000/api/v1 · DB localhost:5432 |
| Staging AWS | **Chưa có.** Cần cho NT-01..03, NT-07, NT-08, NT-12 (OQ-TP-05) |

### 11.3 Dữ liệu kiểm thử

Chiến lược: **synthetic** — không dùng tài liệu hay dữ liệu cá nhân thật (CON-006, BRU-001).

| Bộ | Nguồn | Dùng ở |
|---|---|---|
| Tài khoản mẫu | `app/seed.py`: `lan@demo.local` (Thành viên), `minh@demo.local` (Quản lý), `hung@demo.local` (Quản trị viên, ngoài nhóm), `tuan@demo.local` (ngoài nhóm), `anh@demo.local` (Thành viên, kịch bản gỡ) | Mọi lớp |
| PDF fixture E2E | `web/e2e/fixtures/pdf.ts` (sinh trong bộ nhớ: HopDongKhung 3 tr., PhuLuc2, BaoGia_v3, `.docx`, PDF hỏng, PDF scan 5 trang trắng) | E |
| PDF fixture pytest | `backend/tests/pdf_factory.py` (`make_pdf`, `make_pdf_of_size`) | U, I |
| Corpus đánh giá | `eval/corpus_src.json` → `npm run eval:corpus` (6 PDF tiếng Việt có dấu) | Q, demo |
| Bộ câu hỏi | `eval/questions.yaml` (20 câu; cần 50 — OQ-TP-03) | Q |
| **Cần sinh** (TK-07) | PDF 50 và 200 trang chữ dày; PDF đúng 20 971 520 byte; bộ 50 file (≥ 5 file 200 trang); PDF chứa chuỗi XSS (TC-095); PDF có mật khẩu người dùng | P, I, S |

Đặt lại dữ liệu trước mỗi spec/lượt: `docker compose exec -T api python -m app.seed --reset` (xóa dữ liệu DB `cwd` — chỉ chạy trên máy test).

---

## 12.0 Responsibilities (IEEE 829 §5.12)

| Vai trò | Trách nhiệm |
|---|---|
| QA Lead (owner) | Soạn và duy trì kế hoạch; phân việc; quyết định tạm dừng/tiếp tục; duyệt khối `expect`; viết Test Summary Report |
| QA Engineer | Viết và chạy TC lớp E, Q, P, S; quản lý dữ liệu test (TK-07); ghi lỗi; cập nhật RTM |
| Developer (2 người [GĐ], IMP §3) | Viết test U/I cho code của mình; sửa lỗi; thêm assert theo `gap` trong `test-cases.yaml`; viết `load_qa.py` cùng QA |
| Engineering Lead | Phê duyệt kế hoạch; phân tích kết quả P; xác nhận đóng lỗi bảo mật (RE-5); trả lời OQ-TP-04 |
| Product Owner | Phê duyệt kế hoạch; duyệt AC đã viết lại (OI-T1, OI-T2); nghiệm thu (TK-14); quyết định hoãn (NT-05, NT-06); duyệt ngân sách REAL |
| Trưởng nhóm BD | Cung cấp bộ 50 câu hỏi + đáp án (PDEP-05) |
| 2 thành viên BD (người chấm) | Chấm CSV AC-US007-1, AC-US009-3b theo rubric (PDEP-06) |
| Trưởng phòng CNTT | Môi trường staging và các mục NT-01..03, 07, 08, 12 |

**Ai quản lý dữ liệu test:** QA Engineer. **Ai review kết quả:** QA Lead (mọi lớp), Engineering Lead (P, S), PO (A, Q).

---

## 13.0 Staffing and Training Needs (IEEE 829 §5.13)

| Nhu cầu | Ai | Cách đáp ứng |
|---|---|---|
| Hiểu RAG có trích dẫn: search-result blocks, citations, `CitationFilter`, ngưỡng τ, RRF | QA | Đọc SAD §2.2, Blueprint ALG-03/05; 1 buổi walkthrough với Developer |
| Viết và debug Playwright, SSE | QA | Đọc `web/e2e/helpers.ts`, `backend/tests/sse_helpers.py` |
| pytest async + DB thật | QA | `backend/tests/conftest.py` |
| Rubric chấm "đoạn trích hỗ trợ câu trả lời" và "trả lời đúng" | 2 người chấm BD | 30 phút hướng dẫn + chấm thử 5 câu, so sánh giữa 2 người trước khi chấm thật |
| Đọc kết quả đo hiệu năng (p50/p90, nhiễu) | QA | Engineering Lead hướng dẫn |
| Kiểm tiếng Việt có dấu (chuẩn hóa NFC, `unaccent`) | QA | `chunker.normalize_page`, test_fts_unaccent |

Nhân lực: 1 QA Lead, 1 QA Engineer, 2 Developer [GĐ], 2 người chấm BD × ~1 ngày/lần chấm (PDEP-06).

---

## 14.0 Schedule (IEEE 829 §5.14)

Mốc cố định từ nguồn: bộ câu hỏi 50 câu **2026-11-30** (PDEP-05); người chấm **2026-12-14** (PDEP-06); mở thử nghiệm cho đội BD **2027-01-04** (PRD §5.1). Các ngày khác là **đề xuất**, chờ Owner và PO duyệt (TK-01).

| Mốc | Từ | Đến | Việc | Phụ thuộc |
|---|---|---|---|---|
| M1 Kế hoạch được duyệt | 2026-11-02 | 2026-11-06 | TK-01 | — |
| M2 Chu kỳ 1 xong (xương sống) | 2026-11-09 | 2026-11-13 | TK-03, TK-11 (nếu OI-T3 đã chốt) | M1 |
| M3 Chu kỳ 2 xong (chức năng FAKE) | 2026-11-16 | 2026-11-27 | TK-02, 04, 05, 06, 07, 10 | M2 |
| M4 Có bộ 50 câu | — | 2026-11-30 | TK-08 | PDEP-05 |
| M5 Chu kỳ 3 (Q, P) | 2026-12-01 | 2026-12-11 | TK-09 (phần chạy), TK-12 | M3, M4, OQ-TP-08 |
| M6 Chấm điểm | 2026-12-14 | 2026-12-18 | TK-09 (phần chấm) | PDEP-06 |
| M7 Chu kỳ 4 (hồi quy + nghiệm thu) | 2026-12-21 | 2026-12-24 | TK-13, TK-14 | M6 |
| M8 Test Summary Report, đề xuất go/no-go | — | 2026-12-28 | TK-15 | M7 |
| Ra mắt thử nghiệm | 2027-01-04 | | Chỉ khi EX-1..EX-10 đạt và NT-01..03, NT-07 có kết quả trên staging | OQ-TP-05 |

---

## 15.0 Risks and Contingencies (IEEE 829 §5.15)

Đánh giá đầy đủ ở **Phụ lục B**. Các vùng rủi ro cao nhất và **thứ tự chạy ưu tiên**:

| Thứ tự | Vùng | Vì sao chạy trước | TC chạy đầu tiên |
|---|---|---|---|
| 1 | Phân quyền và tách quyền (F-05) | Lộ dữ liệu là Critical, chặn ra mắt (G-11); test xác định, rẻ | TC-066, 067, 068, 069, 072, 040 |
| 2 | Trích dẫn và loại thông tin không nguồn (F-02) | Giá trị cốt lõi; RSK-001; TR-04 | TC-031..035, 019..029 |
| 3 | Tải lên → Sẵn sàng (F-01) | Đầu vào của mọi tính năng (409 `NO_READY_DOCUMENTS`) | TC-001..005, 016, 043 |
| 4 | Gỡ tài liệu (F-06) | Yêu cầu pháp lý BR-017; xóa xuyên nhiều bảng dễ sót | TC-070, 071 |
| 5 | Chất lượng AI tiếng Việt (F-03, F-04) | TR-03; phụ thuộc bộ 50 câu nên chạy muộn, nhưng chạy thử bộ 20 câu sớm | TC-048, 051, 054, 028 |
| 6 | Hiệu năng (NFR-001, NFR-003) | TR-02, `bge-m3` CPU chậm (IMP §5) | TC-006, PERF-001 |
| 7 | Phần còn lại (F-07..F-10) | Rủi ro thấp | Theo Phụ lục A |

---

## 16.0 Approvals (IEEE 829 §5.16)

| Vai trò | Tên | Quyết định | Ngày | Chữ ký |
|---|---|---|---|---|
| QA Lead (owner) | *(OQ-TP-02)* | ☐ Duyệt ☐ Duyệt có điều kiện ☐ Không duyệt | | |
| Product Owner | *(OQ-TP-02)* | ☐ Duyệt ☐ Duyệt có điều kiện ☐ Không duyệt | | |
| Engineering Lead | *(OQ-TP-02)* | ☐ Duyệt ☐ Duyệt có điều kiện ☐ Không duyệt | | |

Phê duyệt cho phép bắt đầu chu kỳ 2. Mọi thay đổi phạm vi (§4, §5) hoặc ngưỡng (§7) sau khi duyệt cần phê duyệt lại và tăng phiên bản. **Không hạ ngưỡng để cổng đạt.**

---

## Phụ lục A. Ma trận yêu cầu → vùng kiểm thử → test case

Ký hiệu trạng thái TC: **E** = test đã có trong repo · **E+** = đã có, cần thêm assert · **W** = cần viết · **M** = người chấm · **D** = Deferred (NT-xx). Không có cột kết quả — kết quả ở RTM/báo cáo.

### A.1 Tiêu chí chấp nhận (49 AC)

| AC | Ưu tiên | Lớp | TC | Test hiện có / cần viết | TT |
|---|---|---|---|---|---|
| AC-US001-1 → **1a** | P0 | I, E | TC-001..005 | test_single_pdf_ok, test_upper_bounds_accepted, test_worker_happy_path; upload.spec "xác nhận → Sẵn sàng" | E |
| AC-US001-1 → **1b** (NFR-003) | P0 | P | TC-006, TC-007 | `measure_ingest.py --pages 50/200 --runs 3` | E |
| AC-US001-2 | P0 | I, E, Q | TC-008..010 | test_answer_cites_only_source_file; backbone.spec TC-009; run_eval | E |
| AC-US001-3 | P0 | U, I, E | TC-011..014 | test_ask_pending_documents, test_pending_documents_exact_set; AnswerCard; backbone.spec TC-014 | E |
| AC-US001-4 | P0 | U, I, E | TC-015..018 | ClassificationDialog.test; test_requires_classification; backbone.spec TC-018 | E |
| AC-US002-1 | P0 | I, E | TC-036, TC-037 | TC-036 lô 50 PDF → 50 dòng, 100% `ready` (W); batch.spec 3 file (E) | W/E |
| AC-US002-2 | P0 | I | TC-038 | test_batch_one_too_large_others_ok | E |
| AC-US002-3 | P0 | Q | TC-039 | Bộ 50 file (≥ 5 × 200 trang), 1 câu/file, 100% trích dẫn đúng file | W |
| AC-US002-4 | P0 | I, E | TC-040 | test_member_cannot_batch; upload.spec "Lan chọn 2 file" | E |
| AC-US003-1 | P1 | I, E | TC-041, TC-042 | test_list_documents_sorted_desc (E); E2E 5 file: tên, số trang, trạng thái, mới nhất trước (W) | E/W |
| AC-US004-1 | P1 | U, I, E | TC-043, TC-044 | test_not_pdf_magic_bytes, test_worker_pdf_errors, test_pdf_errors; UploadDropzone.test; upload.spec ".docx và PDF hỏng" | E |
| AC-US005-1 | P1 | U, E | TC-045, TC-046 | useDocuments.test (poll ≤ 5 s) (E); E2E % tăng dần tới Sẵn sàng/Lỗi (E+) | E/E+ |
| AC-US006-1 | P0 | E, Q, P | TC-047, PERF-001 | chat.spec gửi bằng Enter; run_eval p90 TTFT ≤ 5 s | E+ |
| AC-US006-2 | P0 | Q | TC-048 | run_eval SC-01 ≥ 80% (cần 20 câu SC-01) | E+ |
| AC-US006-3 | P0 | U, I, E | TC-049 | test_ask_validation_and_permissions; chat.spec "ô nhập rỗng" | E |
| AC-US007-1 | P0 | Q, A | TC-050 | Bộ 50 câu ≥ 80% đúng, 0 mâu thuẫn — người chấm | W/M |
| AC-US007-2 | P0 | I, Q | TC-051 | test_unrelated_question_not_found; câu SC-03 kiến thức phổ thông | E |
| AC-US008-1 | P0 | Q | TC-052 | run_eval SC-02 ≥ 70% (cần 10 câu) | E+ |
| AC-US008-2 | P0 | U, Q | TC-053 | test_two_conflicting_values_both_shown; cặp câu mâu thuẫn trong bộ đánh giá | E |
| AC-US009-1 | P0 | U, I, E, Q | TC-019..023 | test_ask_happy_path_event_order, test_answered_citation_invariants; AnswerCard; chat.spec; run_eval | E |
| AC-US009-2 | P0 | U, I, E | TC-024..027 | test_get_citation_ok_removed_forbidden; test_snippet_max_300; CitationPopover; chat.spec | E |
| AC-US009-3 → **3a** | P0 | I, Q | TC-028, TC-029 | test_snippet_is_on_cited_page; check_grounding.py | E |
| AC-US009-3 → **3b** | P0 | Q | TC-030 | CSV người chấm, 100% `yes` | M |
| AC-US009-4 | P0 | U, I | TC-031..035 | test_citation_filter (16 test); test_uncited_blocks_never_streamed_or_saved; test_all_uncited_becomes_not_found | E |
| AC-US010-1 | P0 | Q | TC-054 | run_eval SC-03 ≥ 9/10 (cần 10 câu) | E+ |
| AC-US010-2 | P0 | U, E | TC-055 | AnswerCard not_found có gợi ý; chat.spec "câu không có trong tài liệu" | E |
| AC-US011-1 | P1 | I, E, Q | TC-056 | test_ask_followup_uses_rewrite; chat.spec "câu hỏi tiếp nối"; câu SC-04 trong eval | E |
| AC-US011-2 | P1 | Q | TC-057 | run_eval SC-04 ≥ 4/5 (cần 5 câu) | E+ |
| AC-US012-1 | P0 | I, E | TC-063 | test_unauthenticated_401; auth.spec "chưa đăng nhập mở / và /admin" | E |
| AC-US012-2 | P0 | U, I, E | TC-064, TC-065 | draftStore.test, RequireAuth.test, test_idle_expired_401 (E); E2E hết phiên khi đang gõ → giữ bản nháp (W) | E/W |
| AC-US013-1 | P0 | I, E | TC-066 | test_list_documents_forbidden_for_outsider_and_admin, test_open_file_forbidden_for_outsider; auth.spec "người ngoài nhóm" | E |
| AC-US013-2 | P0 | I, E | TC-067 | test_admin_lists_metadata_only, test_admin_cannot_open_content; auth.spec "admin không thuộc nhóm" | E |
| AC-US014-1 | P0 | I | TC-068 | test_ask_validation_and_permissions, test_outsider_forbidden_by_require_member | E |
| AC-US014-2 | P0 | I, E | TC-069 | test_revoke_effective_next_request, test_remove_member_effective_next_request; admin.spec "Anh bị gỡ" | E |
| AC-US015-1 | P1 | I, E | TC-082 | test_feedback_*; chat.spec "👎 kèm lý do" | E |
| AC-US015-2 | P1 | I | TC-083 | test_feedback_upsert_replaces_previous | E |
| AC-US016-1 | P2 | I, E | TC-058 | test_new_conversation_no_history; chat.spec "Hội thoại mới" | E |
| AC-US017-1 | P1 | I, E, P | TC-059, TC-060 | test_stop_mid_stream, test_stop_while_llm_thinking (E); chat.spec "Dừng" + đo ≤ 1 s (E+) | E/E+ |
| AC-US018-1 | P1 | U, E | TC-061 | copy.test; chat.spec "Sao chép kèm nguồn" | E |
| AC-US019-1 | P2 | I, E | TC-062 | test_open_file_ok_and_removed, test_open_file_forbidden_for_outsider; chat.spec "mở PDF đúng trang" | E |
| AC-US020-1 | P0 | I, E | TC-070, TC-071 | test_purge_removes_chunks_file_and_redacts_citations, test_purge_then_query_not_found (+ đủ 5 câu) (E+); admin.spec gỡ + đo ≤ 10 s (E+) | E+ |
| AC-US020-2 | P0 | I, E | TC-072 | test_purge_forbidden_for_non_admin, test_admin_routes_forbidden_for_member_and_manager (E); E2E Lan/Minh không thấy thao tác gỡ, mở `/admin` bị chặn (E+) | E/E+ |
| AC-US021-1 | P0 | I, E | TC-073 | test_add_member_then_can_use_content; admin.spec "Hùng thêm thành viên" | E |
| AC-US021-2 | P0 | U, I, E | TC-074 | test_add_member_unknown_email (danh bạ giả lập, ASM-TP-02); admin.test "USER_NOT_FOUND hiện lỗi ngay dưới ô email"; admin.spec "email sai báo lỗi tại ô" | E |
| AC-US021-3 | P0 | I, E | TC-075 | test_remove_member_effective_next_request; admin.spec | E |
| AC-US021-4 | P0 | I | TC-076 | test_role_change_enables_batch_upload | E |
| AC-US021-5 | P0 | U, E | TC-077 | Trang quản trị không có liên kết tới nội dung (admin.test + E2E duyệt mọi link) | W |
| AC-US022-1 | P0 | I, E | TC-078 | test_audit_query_filters_and_cursor, test_audit_includes_member_logins_and_known_flow; admin.spec "nhật ký có các thao tác" | E |
| AC-US022-2 | P0 | I | TC-079 | test_audit_meta_never_contains_content, test_no_content_in_audit_meta, test_audit_meta_has_no_email | E |
| AC-US022-3 | P0 | I, E | TC-080 | Khoảng > 12 tháng → chỉ trả dữ liệu còn lưu + thông báo giới hạn | W |
| AC-US022-4 | P1 | I, E | TC-081 | Xuất CSV UTF-8 đúng bản ghi đã lọc; ghi `audit_export` | D (NT-06) |

**Độ phủ AC:** 49/49 AC có ≥ 1 TC (US-001 và US-009 tính theo bản đã viết lại: 1a, 1b, 3a, 3b). 1 AC Deferred (AC-US022-4).

### A.2 NFR

| NFR | Cách đo | Ngưỡng | TC | TT |
|---|---|---|---|---|
| NFR-001 | Client đo thời điểm gửi → `answer.delta` đầu tiên; p90 trên ≥ 20 câu (1 người) và trên PERF-003 (10 người) | p90 ≤ 5 s | PERF-001, PERF-003, TC-047 | E+/W |
| NFR-002 | Gửi → `answer.completed`; p90 | p90 ≤ 20 s | PERF-002, PERF-003 | E+/W |
| NFR-003 | 202 → `status=ready`, poll 1 s, 3 lần | ≤ 120 s (50 tr.), ≤ 480 s (200 tr.), 3/3 | TC-006, TC-007 | E |
| NFR-004 | Tỷ lệ đúng tách theo `lang`; câu hỏi chéo ngôn ngữ | ≥ 80% mỗi ngôn ngữ (G-06); ≥ 30% câu mỗi ngôn ngữ (G-05) | TC-093 | E+ |
| NFR-005 | 10 người dùng ảo đồng thời | p90 như NFR-001/002; 0 lỗi | PERF-003 | W |
| NFR-006 | 20 câu/phút × 10 phút | p90 như NFR-001/002; 0 lỗi | PERF-004 | W |
| NFR-007 | 50 file × 200 trang, ≤ 1 GB | 100% ready; NFR-001 vẫn đạt | PERF-005 | W |
| NFR-008 | Review SAD §4.4 | — | — (NT-10) | — |
| NFR-009 | Dời `last_seen_at` quá 8 giờ | 401 `SESSION_EXPIRED`; bản nháp giữ lại | TC-064, TC-101 | E |
| NFR-010 | Đối chiếu thao tác đã làm với `audit_log`; kiểm trường | 100% thao tác có bản ghi; 0 nội dung | TC-078, TC-079, TC-016 | E |
| NFR-011 | Gỡ thành viên → request kế tiếp | Bị từ chối ở request kế tiếp (≤ 15 phút) | TC-069, TC-075 | E |
| NFR-012 | Canary trên staging | ≥ 95% giờ làm việc | — (NT-01) | — |
| NFR-013 | Diễn tập khôi phục trên staging | RTO ≤ 1 ngày làm việc; RPO ≤ 24 giờ | — (NT-02) | — |
| NFR-014 | Làm LLM không khả dụng (khóa API sai / chặn mạng tới API) | `answer.failed{AI_UNAVAILABLE}`, thông điệp E-12; danh sách và tải lên vẫn 200/202 | TC-089 | W |

### A.3 Trường hợp biên và launch gate

| Mục | TC | TT |
|---|---|---|
| E-01, E-02 trạng thái trống / tất cả đang xử lý | TC-084 | W |
| E-03, E-04, E-05, E-06, E-07 | TC-043, TC-044, TC-003 | E |
| E-08 bộ đầy 50 file | TC-085 (test_concurrent_last_slot) | E |
| E-09 trùng tên | TC-086 (test_duplicate_name_renamed) | E |
| E-10 mất mạng khi tải lên (thử lại 3 lần) | TC-087 (unit cho `api/documents.ts` retry) | W |
| E-11 mất mạng khi nhận câu trả lời | TC-088 (test_llm_error_mid_stream, test_max_tokens_is_failed; AnswerCard "Tạo lại") | E |
| E-12 dịch vụ AI lỗi | TC-089 | W |
| E-13 giới hạn 30 câu/giờ | — (NT-05) | — |
| E-14 câu hỏi rỗng | TC-049 | E |
| E-15 > 2000 ký tự | TC-090 (test_ask_validation_and_permissions) | E |
| E-16 không tìm thấy | TC-051, TC-054, TC-055 | E |
| E-17 nhiều đáp án / làm rõ | TC-091 (test_clarify_with_citations; câu SC-05 khi có bộ 50 câu) | E/W |
| E-18 hết phiên | TC-064, TC-065 | E/W |
| E-19 không có quyền | TC-066 | E |
| E-20 hai người tải cùng lúc, cập nhật ≤ 10 s | TC-092 | W |
| E-21 ngoài VPN | — (NT-08) | — |
| E-22 tài liệu bị gỡ khi đang được trích dẫn | TC-024, TC-071 | E |
| G-04 Chrome + Edge | TC-097 | W |
| G-11 phân quyền | TC-040, 066..069, 072..077 | E/W |
| G-13 không nội dung trong log | TC-079, TC-094 | E/W |
| G-15 lỗ hổng | TC-096 | W |
| DoD a11y | TC-098, TC-099 | W/E |
| DoD hợp đồng API | TC-100 (đối chiếu response với openapi.json bằng schema validator) | W |

### A.4 Thành phần thiết kế → TC

| Thành phần (SAD) | TC |
|---|---|
| `CitationFilter` (ALG-05) | TC-031..035, TC-053, TC-091 |
| RRF + τ (ALG-03) | test_retriever (10 test), TC-051 |
| Chia đoạn theo trang (ALG-02) | test_chunker (7 test), TC-029 |
| `AccessPolicy` | test_policy_truth_table, TC-066..069 |
| Trạng thái Turn | TC-059 (`stopped`), TC-088 (`incomplete`), TC-019 (`completed`) |
| Trạng thái tài liệu | TC-002, TC-043, test_recover_stuck_processing |
| Trạng thái phiên | TC-064, test_logout_invalidates |
| Gỡ tài liệu §3.2.3 | TC-070, TC-071 |
| QAS-1..QAS-4, QAS-6 | TC-067, TC-069, TC-054, TC-028, PERF-003 |

---

## Phụ lục B. Danh sách rủi ro

Thang Khả năng (K) và Ảnh hưởng (A) 1–5; Điểm = K × A.

| ID | Rủi ro | K | A | Điểm | Giảm thiểu / dự phòng | Owner |
|---|---|---|---|---|---|---|
| RSK-001 *(BRD)* | Câu trả lời bịa đặt / không có nguồn được hiển thị | 4 | 5 | 20 | Ưu tiên 2 ở §15; TC-031..035 chạy mỗi build; G-09 100% | QA Lead |
| RSK-002 *(BRD)* | Lộ tài liệu cho người không có quyền | 4 | 5 | 20 | Ưu tiên 1; gọi API trực tiếp (không chỉ UI); SU-3 dừng toàn bộ | Engineering Lead |
| TR-03 *(SAD)* | Tìm kiếm tiếng Việt chưa đạt G-06/G-07 | 4 | 4 | 16 | Chạy bộ 20 câu sớm (M2); chỉnh τ/top-k, chạy lại toàn bộ bộ câu | Engineering Lead |
| RSK-TP-01 | Bộ 50 câu (PDEP-05) trễ sau 2026-11-30 → không đo được G-05..G-08 đúng cỡ mẫu | 3 | 5 | 15 | Chạy trước trên 20 câu và báo cáo "chưa đủ mẫu"; không tuyên bố đạt gate với < 50 câu | Trưởng nhóm BD |
| RSK-TP-02 | Không có staging trước pilot → NT-01..03, 07 không kiểm được | 3 | 5 | 15 | OQ-TP-05; Test Summary Report ghi rõ "chưa kiểm" cho các gate này | Trưởng phòng CNTT |
| TR-02 *(SAD)* | p90 nội dung đầu tiên > 5 s (thinking luôn bật) | 3 | 4 | 12 | Đo PERF-001 sớm; đòn bẩy do PO quyết (SAD §4.5), không tự đổi model | Product Owner |
| RSK-TP-03 | `bge-m3` trên CPU làm NFR-003 không đạt trên máy test | 4 | 3 | 12 | Chốt máy tham chiếu (OI-T3); phương án API embedding (IMP §5) | Engineering Lead |
| RSK-TP-04 | Lệch giữa openapi.json và bản build (ví dụ: đường dẫn dừng `…/stop` vs `…:stop`, đăng nhập giả lập, `/health` vs `/healthz`, chưa có `/documents/events`, `:batch`, `:export`, `/events`; mã lỗi `USER_NOT_FOUND` vs `USER_NOT_IN_DIRECTORY`) → test hợp đồng TC-100 đỏ hàng loạt | 4 | 3 | 12 | OQ-TP-04: Engineering Lead quyết cập nhật spec hay code trước chu kỳ 2 | Engineering Lead |
| TR-04 *(SAD)* | `CitationFilter` loại nhầm câu đúng | 3 | 3 | 9 | Unit test; theo dõi tỷ lệ khối bị loại trong eval | Developer |
| RSK-TP-05 | E2E chập chờn do dùng chung DB `cwd`, worker poll 2 s, FE poll 3 s | 3 | 3 | 9 | `workers: 1`; seed lại mỗi spec; 3/3 lần; SU-4 | QA |
| RSK-TP-06 | Chi phí gọi Claude thật khi chạy Q/P nhiều lần | 3 | 3 | 9 | OQ-TP-08 ngân sách; `--dry-run` trước; chỉ chạy lại khi đổi cấu hình | Product Owner |
| RSK-TP-07 | Người chấm BD không thống nhất rubric | 2 | 4 | 8 | Chấm thử 5 câu và so sánh trước (§13); bất đồng → PO quyết | QA Lead |
| RSK-TP-08 | Chưa có CI → hồi quy phụ thuộc vào việc chạy tay | 3 | 2 | 6 | REG-001..003 bắt buộc trước mỗi báo cáo (EX-8) | QA Lead |

---

## Phụ lục C. Câu hỏi mở và giả định

### C.1 Câu hỏi mở

| ID | Câu hỏi | Ảnh hưởng | Người trả lời | Hạn |
|---|---|---|---|---|
| OI-T1 | Câu trả lời `clarification` không có trích dẫn có được phép không? | AC-US009-1, TC-091 | Product Owner | 2026-11-06 |
| OI-T2 | Chấp nhận các AC đã viết lại (01-pham-vi-va-ac.md) và chặn ở API AC-US001-4(d) vào PRD? | AC-US001-*, AC-US009-* | Product Owner | 2026-11-06 |
| OI-T3 | Máy tham chiếu cho NFR-003 và PERF (CPU/RAM/GPU)? | TC-006/007, PERF-001..005 | Engineering Lead | 2026-11-06 |
| OQ-TP-01 | Giữ kế hoạch ở `docs/test/` hay chuyển sang `docs/07-verification/` như prompt đề xuất? | Đường dẫn D-01 | QA Lead | 2026-11-06 |
| OQ-TP-02 | Tên người cho Owner và người phê duyệt (§0, §16) | Phê duyệt | Product Owner | 2026-11-06 |
| OQ-TP-03 | Bộ 50 câu hỏi theo G-05 (20 SC-01, 10 SC-02, 10 SC-03, 5 SC-04, 5 SC-05, ≥ 30% mỗi ngôn ngữ) | AC-US006-2, 007-1, 008-1, 010-1, 011-2, G-05..G-08 | Trưởng nhóm BD | 2026-11-30 (PDEP-05) |
| OQ-TP-04 | openapi.json và bản build lệch nhau (RSK-TP-04): sửa spec hay sửa code? Có làm CSRF/CSP theo SAD §2.1 trong bản thử nghiệm không? | TC-100, TC-102 | Engineering Lead | 2026-11-13 |
| OQ-TP-05 | Có môi trường staging trước 2027-01-04 cho NT-01..03, 07, 08, 12 không? | Launch gate G-12, G-18, NFR-012/013 | Trưởng phòng CNTT | 2026-11-16 (PDEP-04) |
| OQ-TP-06 | Hoãn xuất CSV (AC-US022-4, P1) khỏi đợt pilot? | TC-081, EX-2 | Product Owner | 2026-11-06 |
| OQ-TP-07 | Pilot có cần giới hạn 30 câu/giờ và trần chi phí (G-16, E-13) không, khi bản thử nghiệm chưa làm? | NT-05, G-16 | Product Owner | 2026-11-13 |
| OQ-TP-08 | Ngân sách gọi Claude thật cho Q và P | EN-5, SU-5 | Product Owner | 2026-11-13 |
| OQ-TP-09 | Dùng công cụ nào để theo dõi lỗi? | D-09 | QA Lead | 2026-11-06 |

### C.2 Giả định

| ID | Giả định | Nếu sai thì |
|---|---|---|
| ASM-TP-01 | Hồ sơ FAKE cho kết quả xác định; kết quả U/I/E trên FAKE đại diện cho logic không phụ thuộc AI | Thêm lượt E trên REAL cho các hành trình chính |
| ASM-TP-02 | Đăng nhập giả lập và danh bạ giả lập đủ để kiểm logic phân quyền và AC-US021-2; tích hợp Microsoft 365 kiểm riêng (NT-07) | AC-US021-2 và US-012 phải kiểm lại trên staging |
| ASM-TP-03 | AC của US-021, US-022 trong UserStories.md là bản baseline dù chưa có trong PRD (USB-01) | Cập nhật Phụ lục A khi PRD thêm story |
| ASM-TP-04 | Kết quả hiệu năng trên máy local chỉ có giá trị chỉ báo cho môi trường vận hành | Đo lại trên staging trước khi kết luận NFR-001..007 cho pilot |
