# Kế hoạch triển khai — "Chat với tài liệu" (bản thử nghiệm)

> **Đầu vào:** [User Stories](../requirements/UserStories.md) · [SAD](../design/SAD.md) · [Blueprint SDD](../design/Blueprint_SDD.md) · [Thiết kế UI/UX](../design/UI_UX_design/index.html)
> **Task chi tiết:** [docs/implements/tasks/](../implements/tasks/README.md)
> ⚠️ Tài liệu bài tập. Bản này là **bản thử nghiệm chạy local**, tập trung làm ra sản phẩm dùng được để kiểm chứng ý tưởng.

| Thuộc tính | Giá trị |
|---|---|
| Số hiệu | IMP-CWD-001 |
| Phiên bản | 0.2 (2026-10-21): lược giản thành bản thử nghiệm chạy local |
| Người đọc | Developer, QA |

## 1. Mục tiêu

Làm ra một ứng dụng chạy bằng `docker compose up`. Người dùng BD tải PDF lên, hỏi bằng tiếng Việt hoặc tiếng Anh, và nhận câu trả lời streaming **chỉ dựa trên tài liệu**, mỗi thông tin có **trích dẫn tên file và số trang**. Quản trị viên quản lý thành viên, gỡ tài liệu và xem nhật ký, nhưng không thấy nội dung tài liệu.

Bản thử nghiệm phủ đủ **22 user story**. Các yêu cầu cần hạ tầng thật (thời gian hoạt động, giới hạn chi phí, dọn dữ liệu, Microsoft 365) để lại cho bản chính thức.

## 2. Khác biệt so với thiết kế gốc (SAD)

| Thiết kế gốc | Bản thử nghiệm | Lý do |
|---|---|---|
| AWS: ECS, RDS, S3, SQS, Bedrock | Docker Compose local: PostgreSQL + pgvector, ổ đĩa local, worker đọc job từ bảng `documents` | Không cần tài khoản đám mây để chạy thử |
| Claude trên Bedrock, Cohere Embed | Claude qua Anthropic API; embedding `bge-m3` chạy local | Ít phụ thuộc; giữ nguyên cách dùng search-result blocks + citations |
| Đăng nhập Microsoft 365 (OIDC) | Đăng nhập giả lập bằng tài khoản mẫu | Không cần app registration |
| SSE trạng thái tài liệu qua NOTIFY | Frontend hỏi lại danh sách mỗi 3 giây | Vẫn đạt yêu cầu "cập nhật ít nhất mỗi 5 giây" (AC-US005-1) |
| Clean Architecture 4 tầng, `import-linter` | Module theo tính năng (`router` / `service`), các gateway AI tách riêng để test | Ít mã khung hơn |
| CI/CD, Terraform, giám sát, canary, analytics, giới hạn chi phí, dọn dữ liệu, xuất CSV | Không làm | Ngoài mục tiêu thử nghiệm |

**Giữ nguyên** các phần làm nên chất lượng sản phẩm:
- Chia đoạn theo trang (ALG-02).
- Tìm kiếm kết hợp vector và từ khóa bằng RRF (ALG-03).
- `CitationFilter` (ALG-05).
- Phân quyền ba vai trò, trong đó admin không thấy nội dung.
- Gỡ tài liệu xóa cả trích dẫn đã lưu.
- Không log nội dung.

## 3. Lộ trình [GĐ: 2 developer]

| Tuần | Kết quả demo được | Task |
|---|---|---|
| 1 | Chạy được local; đăng nhập; tải PDF lên và thấy trạng thái chuyển sang *Sẵn sàng* | T-01 → T-07 |
| 2 | Hỏi đáp streaming có trích dẫn; "không tìm thấy"; câu hỏi tiếp nối; dừng | T-08 → T-11 |
| 3 | Đánh giá 👍/👎, quản trị thành viên, gỡ tài liệu, nhật ký; bộ câu hỏi đánh giá đạt mục tiêu; demo | T-12 → T-15 |

Thứ tự phụ thuộc và ước lượng chi tiết nằm ở [README của thư mục task](../implements/tasks/README.md#3-danh-sách-task).

## 4. Tiêu chí hoàn thành bản thử nghiệm

- Mọi tiêu chí chấp nhận của 22 story đạt khi QA chạy tay. Riêng các AC đo trên bộ câu hỏi kiểm thử được chạy trên bộ đánh giá nhỏ (T-15).
- Bộ đánh giá nhỏ đạt mục tiêu:
  - ≥ 80% câu trả lời đúng (G-06).
  - ≥ 9/10 câu không có trong tài liệu nhận "không tìm thấy" (G-08).
  - 100% trích dẫn đúng trang trên mẫu kiểm tra (G-09).
- Nội dung đầu tiên hiển thị trong ≤ 5 giây với một người dùng.
- Trên đường đi của mã không có chỗ nào log câu hỏi, câu trả lời hay đoạn văn.
- Người mới clone repo chạy được theo README trong ≤ 30 phút.

## 5. Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| `bge-m3` chạy CPU chậm với tài liệu dài | Đo ở T-06; nếu quá chậm thì chuyển sang API embedding (chỉ thay `embeddings.py`) |
| Tìm kiếm tiếng Việt chưa đủ tốt | Chỉnh `retrieval_top_k`, `retrieval_not_found_tau` bằng bộ đánh giá ở T-15 |
| `CitationFilter` loại nhầm câu đúng | Có unit test riêng; theo dõi trong bộ đánh giá |
| Chi phí gọi Claude khi thử nghiệm | Model đặt trong cấu hình (`llm_model`), có thể đổi sang model rẻ hơn khi chạy thử nhiều |
