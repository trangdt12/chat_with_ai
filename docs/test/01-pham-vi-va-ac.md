# Phạm vi kiểm thử và tiêu chí chấp nhận đã chốt

> Đầu vào: [UserStories.md](../requirements/UserStories.md) (AC nguyên văn PRD v0.4) · [bối cảnh Day 5](00-boi-canh-day5.md).
> Quy tắc: AC nào chưa đo được thì **viết lại cho đo được trước khi viết test**, không để người chạy test tự diễn giải.

## 1. Hai user story xương sống

| Story | Vì sao chọn |
|---|---|
| **US-001 · Tải một file PDF lên** (P0) | Đầu vào của mọi tính năng: chưa có tài liệu "Sẵn sàng" thì không hỏi được (`409 NO_READY_DOCUMENTS`). Đi qua cả 3 tiến trình: api, worker, web. |
| **US-009 · Trích dẫn tên tài liệu và số trang** (P0) | Giá trị cốt lõi của sản phẩm (BR-008, BRU-006): người dùng chỉ dùng được câu trả lời khi đối chiếu được nguồn. Là đầu ra cuối của luồng hỏi đáp (retriever → Claude → CitationFilter → popover). |

Hai story này nối thành một đường đi trọn: **tải PDF → Sẵn sàng → hỏi → câu trả lời có `[n]` → đoạn trích nằm đúng trang**.
Các story hỏi đáp còn lại (US-006, 007, 008, 010) đo chất lượng câu trả lời bằng thống kê trên bộ câu hỏi; chúng nằm ngoài đợt này (xem non-goals trong [test plan](02-test-plan.md)).

## 2. AC đã sửa

Cột "Vấn đề" giải thích vì sao bản gốc chưa đo được. Bản sửa là **đề xuất**, cần PO duyệt rồi cập nhật vào PRD/UserStories (tài liệu đó đang ghi "nguyên văn PRD").

### US-001

| AC | Bản gốc (tóm tắt) | Vấn đề | Bản đã chốt để test |
|---|---|---|---|
| **AC-US001-1a** | File PDF hợp lệ ≤ 200 trang, ≤ 20 MB → hiện "Đang xử lý", rồi "Sẵn sàng" | (1) "hợp lệ" không định nghĩa. (2) "20 MB" không rõ 20·10⁶ hay 20·2²⁰ byte; code dùng 20 971 520. (3) Trạng thái đầu tiên trong UI là **"Đã tải lên"**, không phải "Đang xử lý"; với file nhỏ có thể không bao giờ thấy "Đang xử lý" → test sẽ chập chờn. (4) Gộp yêu cầu chức năng với hiệu năng. | *Cho trước* Lan là thành viên bộ tài liệu và đã xác nhận phân loại trong phiên; *khi* Lan tải 1 file PDF **đọc được bằng pypdf, không mật khẩu người dùng, có lớp chữ, 1–200 trang, ≤ 20 971 520 byte**; *thì* (a) API trả `200`, phần tử kết quả có `status="uploaded"`, `id` khác null, `error_code=null`; (b) chuỗi trạng thái quan sát được qua `GET /documents` là dãy con của `uploaded → processing → ready`, `progress` không giảm; (c) trạng thái cuối là `ready`, `progress=100`, `pages` = số trang thật; (d) dòng tài liệu trên UI hiện "Sẵn sàng" **mà không tải lại trang**. |
| **AC-US001-1b** | "…trong thời gian theo NFR-003" | Không nêu môi trường, cách đo, số lần đo. Không có cột `ready_at` nên phải đo từ client. | *Cho trước* hồ sơ REAL (`EMBED_FAKE=0`, model bge-m3 đã nạp, worker rảnh, máy tham chiếu ghi trong báo cáo); *khi* tải 1 PDF có chữ; *thì* thời gian từ lúc API trả `200` đến lúc `GET /documents` trả `status="ready"` (poll 1 s) **≤ 120 s với file 50 trang** và **≤ 480 s với file 200 trang**, ở **cả 3/3 lần đo** (không lấy trung bình). |
| **AC-US001-2** | Hỏi về nội dung chỉ có trong file đó → câu trả lời lấy từ file đó, trích dẫn tên file đó | Với bộ chỉ có 1 file thì luôn đúng, không chứng minh gì. "Lấy từ file đó" không có tiêu chí máy. | *Cho trước* bộ tài liệu có **≥ 2 file "Sẵn sàng"** và thông tin X chỉ có trong file F; *khi* Lan hỏi về X; *thì* `answer.completed.answer_type="answered"` và **≥ 1 trích dẫn có `filename = F`**. Ở hồ sơ REAL thêm: câu trả lời (chuẩn hóa) chứa giá trị kỳ vọng của X. |
| **AC-US001-3** | ≥ 1 "Sẵn sàng" và ≥ 1 "Đang xử lý" → ghi chú nêu tên file chưa dùng | "Đang xử lý" có gồm file đang chờ (`uploaded`) không? File lỗi có được nêu không? | *Cho trước* ≥ 1 file `ready` và ≥ 1 file `uploaded` hoặc `processing`; *khi* Lan hỏi; *thì* (a) tập `answer.completed.pending_documents[].filename` **bằng đúng** tập tên file đang `uploaded`/`processing` lúc hỏi (file `failed` không có mặt); (b) không trích dẫn nào trỏ tới file trong tập đó; (c) UI hiện ghi chú "Tài liệu sau chưa được dùng để trả lời vì đang xử lý:" kèm đủ các tên. Áp dụng cả khi `answer_type="not_found"`. |
| **AC-US001-4** | Lần đầu trong phiên, chưa tích xác nhận → nút tải lên bị vô hiệu; xác nhận được ghi nhật ký | Chỉ chặn ở UI thì gọi thẳng API là vượt qua được BRU-001. "Ghi vào nhật ký" không nói ghi gì. | (a) Lần tải đầu trong phiên: hộp thoại "Xác nhận phân loại tài liệu" hiện, nút "Xác nhận và tải lên" `disabled` cho tới khi tích ô; (b) sau khi xác nhận: có **đúng 1** dòng `audit_log` `action="classification_confirm"` với `user_id` và `doc_set_id` tương ứng; (c) lần tải sau trong cùng phiên: không hiện hộp thoại; phiên mới: hiện lại; (d) **[bổ sung, cần PO duyệt]** gọi API tải lên khi phiên chưa xác nhận → `409 CLASSIFICATION_REQUIRED` và không tạo dòng `documents` nào. |

### US-009

| AC | Bản gốc (tóm tắt) | Vấn đề | Bản đã chốt để test |
|---|---|---|---|
| **AC-US009-1** | Câu trả lời có nội dung → ≥ 1 trích dẫn gồm tên tài liệu và số trang | "Có nội dung" không định nghĩa. Câu trả lời loại `clarification` có thể không có nguồn (CitationFilter cho phép) → mâu thuẫn nếu tính là "có nội dung". | *Cho trước* `answer.completed.answer_type="answered"`; *thì* `citations` có ≥ 1 phần tử, mỗi phần tử có `filename` khác rỗng và `page` nguyên với `1 ≤ page ≤ documents.pages`; UI có ≥ 1 nút "Nguồn n: <file> trang <p>" trong thân câu trả lời và danh sách "Nguồn" có "<file> · trang <p>". *Loại `clarification` không nguồn: câu hỏi mở OI-T1, ngoài phạm vi.* |
| **AC-US009-2** | Bấm trích dẫn → đoạn văn nguồn ≤ 300 ký tự kèm tên file, số trang | Đo được; chỉ cần nói rõ đơn vị và nguồn so sánh. | *Khi* bấm `[n]` (hoặc `GET /citations/{id}`); *thì* API trả `200`, `snippet` dài **1–300 ký tự Unicode**, `filename`, `page`, `document_id` **trùng** với trích dẫn trong sự kiện SSE; popover hiện "<file> · trang <p>" và đoạn trích. |
| **AC-US009-3a** | 20 câu trả lời ngẫu nhiên, QA đối chiếu thủ công, 100% thông tin có ở trang đã nêu | "Ngẫu nhiên" không tái lập được; bộ eval chỉ có 16 câu loại trả lời; "đối chiếu thủ công" không phải tiêu chí máy. | *Cho trước* một lượt chạy `run_eval.py` ở hồ sơ REAL; *với* **mọi trích dẫn của mọi lượt `answered`**; *thì* `norm(snippet)` là chuỗi con của `norm(text trang page của file)` (đọc lại bằng pypdf; `norm` = `normalize_page` + gộp khoảng trắng + chữ thường). Ngưỡng **100%**, tối thiểu 16 lượt được kiểm. |
| **AC-US009-3b** | (phần ngữ nghĩa của bản gốc) | Máy chỉ kiểm được "đoạn trích có ở trang đó", không kiểm được "câu trả lời được đoạn trích hỗ trợ". | *Với* mọi cặp (đoạn câu trả lời, trích dẫn) của lượt chạy ở 3a; người chấm điền `supports = yes/no` theo rubric: *"chỉ dựa vào snippet, có suy ra được đúng nội dung của đoạn câu trả lời không?"*; *thì* **100% `yes`**. Kết quả ghi vào CSV để máy đọc. |
| **AC-US009-4** | Thông tin không xác định được nguồn → không xuất hiện; nếu mọi thông tin bị loại → "không tìm thấy" | "Thông tin" chưa định nghĩa. Code giữ lại câu nối ngắn giữa hai khối có nguồn → bản gốc nói "không xuất hiện" sẽ làm test đúng thành sai. | *Cho trước* Claude trả một khối văn bản **không có trích dẫn hợp lệ** (không có citation, hoặc `search_result_index` ngoài phạm vi); *thì* nội dung khối đó **không có** trong bất kỳ `answer.delta` nào và không có trong `turns.answer`. *Ngoại lệ:* khối nằm giữa hai khối có nguồn và thỏa `is_connective` (≤ 12 từ, không có chữ số, < 30% từ viết hoa) thì được giữ. Nếu không khối nào có trích dẫn hợp lệ (và không có marker làm rõ) → `answer_type="not_found"`, không có `answer.delta`, `turns.answer=""`. |

## 3. Câu hỏi mở phát sinh

| ID | Câu hỏi | Ảnh hưởng |
|---|---|---|
| OI-T1 | Câu trả lời `clarification` không có trích dẫn có được phép không? (mâu thuẫn tiềm ẩn giữa AC-US009-1 và hành vi CitationFilter) | Ngoài phạm vi đợt này; cần PO quyết |
| OI-T2 | AC-US001-4(d) chặn ở API là bổ sung mới — PO có chấp nhận đưa vào PRD? | Code đã làm; test chạy, nhưng nếu PO bỏ thì TC-016 chuyển sang regression |
| OI-T3 | Máy tham chiếu cho NFR-003 là máy nào (CPU/RAM, có GPU không)? | Chưa chốt thì AC-US001-1b chỉ ghi kết quả "không kết luận" |
