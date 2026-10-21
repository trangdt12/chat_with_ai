# T-15 · Kiểm thử end-to-end, bộ câu hỏi đánh giá nhỏ, kịch bản demo

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| Mọi story; đo gần đúng AC-US006-2, AC-US007-1, AC-US008-1, AC-US009-3, AC-US010-1, AC-US011-2 | Tất cả task trước | 2 ngày |

## 1. Mục tiêu
Chứng minh sản phẩm chạy đúng từ đầu đến cuối, gồm 3 phần:
- Bộ test Playwright cho luồng chính, chạy với fake LLM nên ổn định và không tốn tiền.
- Bộ ~20 câu hỏi đánh giá chạy với Claude thật, có script chấm và báo cáo, để biết chất lượng trả lời ở mức nào.
- Kịch bản demo 15 phút theo 3 persona Lan, Minh, Hùng.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `web/e2e/playwright.config.ts` | `baseURL` = `http://localhost:5173`; backend chạy với `LLM_FAKE=1`, `EMBED_FAKE=1` |
| `web/e2e/fixtures/*.pdf` | 3 PDF nhỏ có chữ (hợp đồng, phụ lục, báo giá) + 1 file `.docx` + 1 PDF hỏng + 1 PDF scan |
| `web/e2e/*.spec.ts` | Các spec ở §2.2 |
| `backend/app/qa/llm.py`, `backend/app/ingestion/embeddings.py` | Nếu chưa có: `FakeLlm`, `FakeEmbedder` bật bằng biến môi trường (dùng chung với pytest) |
| `eval/corpus/` | 5–8 PDF mẫu tiếng Việt và tiếng Anh (tự soạn, không dùng tài liệu thật của công ty) |
| `eval/questions.yaml` | ~20 câu hỏi kèm đáp án |
| `eval/run_eval.py` | Chạy bộ câu hỏi qua API thật, ghi kết quả |
| `eval/reports/YYYY-MM-DD.md` | Báo cáo sinh ra |
| `docs/implements/demo-script.md` | Kịch bản demo |

### 2.2 Chi tiết

**Spec Playwright** (mỗi spec tự seed qua `python -m app.seed --reset`):
| Spec | Luồng |
|---|---|
| `auth.spec.ts` | Chưa đăng nhập mở `/` → về trang đăng nhập; đăng nhập Lan → thấy bộ tài liệu; người ngoài nhóm → trang không có quyền |
| `upload.spec.ts` | Lan: hộp xác nhận phân loại → tải PDF → "Đang xử lý" → "Sẵn sàng"; `.docx` và PDF hỏng báo lỗi riêng; Lan chọn 2 file → bị từ chối, hướng dẫn tải từng file |
| `batch.spec.ts` | Minh tải 3 file một lần → 3 dòng trạng thái riêng → đều "Sẵn sàng" |
| `chat.spec.ts` | Hỏi → stream → `[1]` → popover → mở PDF (tab mới, URL có `#page=`); câu hỏi tiếp nối; Dừng; Sao chép; Hội thoại mới; 👎 kèm lý do |
| `admin.spec.ts` | Hùng thêm/gỡ thành viên; Anh bị gỡ → request kế tiếp ra trang không có quyền; gỡ tài liệu → biến khỏi danh sách của Lan; nhật ký có các thao tác vừa làm |

`FakeLlm` trả theo kịch bản: câu hỏi chứa "không có" → `[KHONG_TIM_THAY]`; còn lại trả 2 khối văn bản, mỗi khối trích dẫn search result đầu tiên, có `sleep(0.2)` giữa các khối để test được nút Dừng.

**Bộ câu hỏi** (`eval/questions.yaml`):
```yaml
- id: Q01
  type: SC-01          # SC-01 một tài liệu · SC-02 nhiều tài liệu · SC-03 không có trong tài liệu · SC-04 câu hỏi tiếp nối
  lang: vi
  question: "Thời hạn thanh toán trong hợp đồng khung là bao lâu?"
  expected: ["30 ngày"]                 # các ý bắt buộc phải có (so khớp không phân biệt hoa thường, bỏ dấu chấm)
  sources: [{file: "HopDongKhung.pdf", page: 14}]
- id: Q15
  type: SC-04
  history: ["Thời hạn thanh toán trong hợp đồng khung là bao lâu?"]
  question: "Điều khoản đó có ngoại lệ không?"
  expected: ["chậm giao hàng"]
  sources: [{file: "HopDongKhung.pdf", page: 15}]
```
Phân bổ: 8 câu SC-01 (≥ 2 câu tiếng Anh, 1 câu hỏi chéo ngôn ngữ), 4 SC-02 (có 1 cặp giá trị mâu thuẫn), 4 SC-03 (gồm 1 câu kiến thức phổ thông, ví dụ "Thủ đô của Pháp là gì?"), 4 SC-04.

**Script chấm** `python eval/run_eval.py --base-url http://localhost:8000 --user lan.nt@congty.vn`:
1. Đăng nhập dev, tải `eval/corpus/` lên một bộ tài liệu riêng `Eval`, chờ tất cả "Sẵn sàng".
2. Với mỗi câu: tạo hội thoại, gửi `history` (nếu có) rồi gửi câu hỏi, gom SSE.
3. Chấm tự động:
   | Chỉ số | Cách tính | Ngưỡng tham khảo |
   |---|---|---|
   | Đúng (SC-01, SC-02, SC-04) | `answer_type = answered` và mọi `expected` có trong câu trả lời | ≥ 80% (SC-01), ≥ 70% (SC-02), ≥ 4/5 (SC-04) |
   | Không tìm thấy (SC-03) | `answer_type = not_found` | ≥ 3/4 |
   | Trích dẫn đúng | Mọi `sources` kỳ vọng có trong `citations` (đúng file và trang) | 100% |
4. Ghi `eval/reports/<ngày>.md`: bảng từng câu (id, loại, đạt/không, độ trễ tới chữ đầu tiên, số trích dẫn) và tổng hợp theo loại. Báo cáo **không** chứa câu trả lời đầy đủ, chỉ ghi đạt/không và các ý bị thiếu.
5. Câu không đạt được người chấm xem lại thủ công; nếu là lỗi chấm (diễn đạt khác nhưng đúng) thì đánh dấu `manual_pass` trong báo cáo.

Nếu tỷ lệ SC-03 thấp hoặc câu đúng bị chặn, chỉnh `retrieval_not_found_tau` trong `.env` rồi chạy lại. Ghi giá trị đã dùng vào báo cáo.

**Kịch bản demo** (`docs/implements/demo-script.md`, ~15 phút):
1. **Lan (Thành viên):** đăng nhập → xác nhận phân loại → tải 1 PDF, xem tiến trình → hỏi câu SC-01 → bấm `[1]` xem đoạn trích, mở PDF gốc → hỏi tiếp nối → hỏi câu ngoài tài liệu ("không tìm thấy") → dừng một câu trả lời dài → sao chép kèm nguồn → 👎 kèm lý do.
2. **Minh (Quản lý):** tải lô 5 file (1 file hỏng) → hỏi câu tổng hợp nhiều tài liệu, chỉ ra 2 giá trị mâu thuẫn kèm nguồn.
3. **Hùng (Admin):** thử mở nội dung → không được → thêm thành viên mới, gỡ Phạm Đức Anh (Anh bị từ chối ngay) → gỡ một tài liệu (trích dẫn cũ báo "đã được gỡ") → tra nhật ký thấy toàn bộ thao tác ở trên.

Chuẩn bị trước: `docker compose up`, `python -m app.seed --reset`, tải sẵn bộ corpus để không phải chờ embedding khi demo.

## 3. Tiêu chí hoàn thành
- [ ] Cả 5 spec Playwright xanh khi chạy `pnpm e2e` trên máy local sạch.
- [ ] Bộ đánh giá chạy hết bằng một lệnh và sinh báo cáo; kết quả được ghi trong báo cáo kể cả khi chưa đạt ngưỡng.
- [ ] Mọi tiêu chí chưa đạt có ghi chú nguyên nhân và đề xuất (chỉnh τ, chunk, prompt).
- [ ] Kịch bản demo được chạy thử trọn vẹn ít nhất 1 lần.

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `pnpm e2e` | 5 spec pass |
| `pytest backend/tests` | Toàn bộ unit/integration xanh trước khi chạy e2e |
| `python eval/run_eval.py --dry-run` | Kiểm tra cú pháp YAML, đủ file corpus, không gọi API |

## 5. Ghi chú
- Mỗi lần chạy bộ đánh giá gọi Claude khoảng 20–30 lần, chi phí nhỏ, nhưng vẫn không đưa vào test tự động chạy thường xuyên.
- Đây là bộ đo nhỏ. Bộ 50 câu chính thức (G-05..G-09) làm khi đi tiếp lên bản chính thức.
