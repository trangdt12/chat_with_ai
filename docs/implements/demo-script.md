# Kịch bản demo — "Chat với tài liệu" (~15 phút)

Ba vai trò: **Lan** (Thành viên BD), **Minh** (Quản lý bộ tài liệu), **Hùng** (Quản trị viên, không thuộc nhóm).
Mở 3 cửa sổ trình duyệt riêng (hoặc 1 cửa sổ thường + 2 cửa sổ ẩn danh) để mỗi người một phiên.

## Chuẩn bị (trước buổi demo)

```bash
cp .env.example .env                 # điền ANTHROPIC_API_KEY; LLM_FAKE=0, EMBED_FAKE=0 để dùng Claude + bge-m3 thật
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed --reset
cd web && npx playwright install chromium && npm run eval:corpus   # sinh PDF mẫu vào eval/corpus/
```

- Tải sẵn **HopDongKhung.pdf, PhuLuc2.pdf, KeHoachTrienKhai.pdf** (trong `eval/corpus/`) bằng tài khoản Minh và chờ "Sẵn sàng", để không phải chờ embedding lần đầu khi demo (lần đầu worker tải model bge-m3 ~2,2 GB).
- Để riêng **BaoGia_v3.pdf** cho Lan tải trong buổi demo, và **DieuKhoanBaoMat.pdf, ServiceLevelAgreement.pdf** + 1 file hỏng (đổi đuôi một file `.docx` thành `.pdf`) cho lô của Minh.
- Chạy thử trọn kịch bản ít nhất 1 lần; nếu mạng yếu, bật `LLM_FAKE=1` làm phương án dự phòng (câu trả lời giả nhưng đủ luồng).

## 1. Lan — Thành viên (≈ 7 phút)

| # | Thao tác | Điểm cần nói | Story |
|---|---|---|---|
| 1 | Mở http://localhost:5173 → chọn **Nguyễn Thị Lan** | Đăng nhập giả lập thay Microsoft 365; header hiện tên và "Dự án X" | US-012 |
| 2 | Kéo thả **BaoGia_v3.pdf** vào thanh bên trái | Lần đầu trong phiên phải **xác nhận phân loại**: nút bị khóa tới khi tích ô | US-001 AC-4 |
| 3 | Xác nhận → xem dòng "Đang tải lên %" → "Đang xử lý n%" → "Sẵn sàng" | Tự cập nhật, không tải lại trang | US-005 |
| 4 | Hỏi: *"Thời hạn thanh toán trong hợp đồng khung là bao lâu?"* | Câu trả lời hiện dần, có `[1]` và danh sách **Nguồn** | US-006, US-009 |
| 4b | Hỏi: *"Giá gói phần mềm bản quyền trong báo giá phiên bản 3 là bao nhiêu?"* | Trích dẫn BaoGia_v3.pdf vừa tải (dùng lại ở phần Hùng, bước 6) | US-001 AC-2 |
| 5 | Bấm `[1]` ở câu trả lời số 4 | Popover: đoạn trích ≤ 300 ký tự, tên file, trang | US-009 AC-2 |
| 6 | Bấm **Mở tài liệu gốc tại trang 2** | Tab mới mở PDF đúng trang | US-019 |
| 7 | Hỏi tiếp: *"Điều khoản đó có ngoại lệ không?"* | Hiểu "điều khoản đó" từ lượt trước → trả lời về chậm giao hàng | US-011 |
| 8 | Hỏi: *"Thủ đô của Pháp là gì?"* | **Không tìm thấy** + 2 gợi ý — không dùng kiến thức ngoài tài liệu | US-010 |
| 9 | Hỏi: *"Tóm tắt toàn bộ nghĩa vụ của các bên trong hợp đồng khung"* → bấm **Dừng** sau 1–2 giây | Dừng ngay, giữ phần đã hiện, nhãn "Đã dừng…", ô nhập dùng được | US-017 |
| 10 | Ở câu trả lời số 4, bấm **Sao chép kèm nguồn** → dán vào Notepad | Văn bản thuần, chỉ số `[1]`, danh sách nguồn ở cuối | US-018 |
| 11 | Bấm 👎 → chọn "Thiếu thông tin" → **Gửi đánh giá** | Nút 👎 được đánh dấu; mỗi người 1 đánh giá cho mỗi câu | US-015 |

## 2. Minh — Quản lý bộ tài liệu (≈ 4 phút)

| # | Thao tác | Điểm cần nói | Story |
|---|---|---|---|
| 1 | Đăng nhập **Trần Văn Minh**, chọn cùng lúc 3 file: DieuKhoanBaoMat.pdf, ServiceLevelAgreement.pdf, file hỏng | Chỉ Quản lý được tải lô; mỗi file một dòng trạng thái | US-002 |
| 2 | Xem bảng **Kết quả tải lô** | Sẵn sàng / Đang xử lý / Lỗi khi xử lý; file hỏng có gợi ý "Xuất lại PDF", không chặn các file khác | US-002 AC-2, US-004 |
| 3 | Hỏi: *"Thời hạn thanh toán là bao nhiêu ngày theo hợp đồng khung và theo phụ lục 2?"* | Nêu **cả hai giá trị mâu thuẫn** (30 và 45 ngày), mỗi giá trị kèm nguồn riêng | US-008 |

## 3. Hùng — Quản trị viên (≈ 4 phút)

| # | Thao tác | Điểm cần nói | Story |
|---|---|---|---|
| 1 | Đăng nhập **Phạm Văn Hùng** | Vào thẳng trang quản trị; **không** có lối tắt tới hỏi đáp hay nội dung tài liệu | US-013 AC-2, US-021 AC-5 |
| 2 | Tab **Nhóm truy cập** → Thêm thành viên `nobody@demo.local` | Báo lỗi ngay dưới ô email, nhóm không đổi | US-021 AC-2 |
| 3 | Thêm **tuan@demo.local** với vai trò Thành viên | Dòng mới xuất hiện; ghi nhật ký | US-021 AC-1 |
| 4 | Gỡ **Phạm Đức Anh** (nhờ một người đăng nhập Anh ở cửa sổ khác trước đó) → Anh bấm tải lại | Anh bị từ chối ngay ở thao tác kế tiếp, thấy trang "không có quyền" | US-021 AC-3, US-014 |
| 5 | Tab **Gỡ tài liệu** → gỡ **BaoGia_v3.pdf** (điền người yêu cầu, lý do, tích xác nhận) | Chỉ thấy thông tin mô tả; nút "Gỡ vĩnh viễn" chỉ bật khi đủ thông tin | US-020 |
| 6 | Quay lại cửa sổ Lan: tài liệu biến khỏi danh sách; bấm `[n]` của câu trả lời cũ trích BaoGia_v3 | Popover: "Tài liệu đã được gỡ khỏi bộ tài liệu" | US-020 AC-1 |
| 7 | Tab **Nhật ký truy cập** → Tra cứu | Thấy đủ: đăng nhập, xác nhận phân loại, tải lên, hỏi đáp, xem trích dẫn, thêm/gỡ thành viên, gỡ tài liệu — **không** có câu hỏi hay nội dung | US-022 |

## Câu hỏi thường gặp khi demo

- *"Nếu tài liệu không có thông tin thì sao?"* → bước 1.8: trả lời "không tìm thấy", không bịa.
- *"Có lộ dữ liệu ra ngoài không?"* → nhật ký không lưu câu hỏi/câu trả lời; admin không xem được nội dung; bản thử nghiệm chạy local, chỉ gửi đoạn văn liên quan tới Claude API.
- *"Chất lượng trả lời thế nào?"* → mở báo cáo mới nhất trong `eval/reports/` (bộ 20 câu, chạy bằng `python /eval/run_eval.py`).
