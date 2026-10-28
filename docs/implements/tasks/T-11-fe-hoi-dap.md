# T-11 · FE hỏi đáp: streaming, trích dẫn, các trạng thái, sao chép, mở PDF

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-006, US-007, US-008, US-009 (AC-1, 2), US-010 (AC-2), US-016, US-017, US-018, US-019; AC-US001-3, AC-US012-2 | T-07, T-10 | 3 ngày |

## 1. Mục tiêu
Lan gõ câu hỏi, thấy câu trả lời hiện dần kèm chỉ số trích dẫn `[n]`, bấm vào `[n]` xem đoạn trích ≤ 300 ký tự và mở PDF gốc đúng trang. Lan dừng được câu trả lời đang tạo, sao chép câu trả lời kèm nguồn và bắt đầu hội thoại mới. Mọi trạng thái đặc biệt (không tìm thấy, cần làm rõ, đã dừng, gián đoạn) hiển thị đúng như thiết kế.

Màn tham chiếu: [05 Hỏi đáp](../../design/UI_UX_design/05-hoi-dap.html), [06 Trích dẫn](../../design/UI_UX_design/06-trich-dan.html), [07 Trạng thái câu trả lời](../../design/UI_UX_design/07-trang-thai-cau-tra-loi.html). Bỏ trạng thái "Giới hạn 30 câu/giờ" (không làm ở bản thử nghiệm).

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `web/src/api/sse.ts` | `streamAnswer()`: đọc SSE từ `fetch` POST bằng `ReadableStream` |
| `web/src/api/types.ts` | Kiểu `AnswerEvent`, `CitationRef`, `Turn` |
| `web/src/pages/ChatPage.tsx` | Bố cục: `DocumentSidebar` (T-07) + `ChatThread` + `Composer` |
| `web/src/components/ChatThread.tsx` | Danh sách lượt; tự cuộn xuống khi có delta |
| `web/src/components/AnswerCard.tsx` | Nội dung (markdown giới hạn), chỉ số `[n]`, danh sách "Nguồn", ghi chú tài liệu chưa sẵn sàng, nhãn trạng thái, nút "Sao chép kèm nguồn" |
| `web/src/components/CitationPopover.tsx` | Gọi `GET /citations/{id}`; hiển thị đoạn trích, tên file, trang, nút "Mở tài liệu gốc tại trang N"; trạng thái đã gỡ |
| `web/src/components/Composer.tsx` | Ô nhập; Enter gửi, Shift+Enter xuống dòng; nút Gửi ↔ Dừng; dòng nhắc cố định |
| `web/src/state/chat.ts` | Hook `useChat(docSetId)` giữ `conversationId`, danh sách lượt, lượt đang stream |

### 2.2 Chi tiết

**Đọc SSE** (không dùng `EventSource` vì cần POST):
```ts
type CitationRef = { idx: number; citation_id: string; document_id: string | null; filename: string | null; page: number };
type AnswerEvent =
  | { event: "answer.started"; data: { message_id: string; turn_index: number } }
  | { event: "answer.delta"; data: { text: string; citations: CitationRef[] } }
  | { event: "answer.completed"; data: { message_id: string; answer_type: "answered" | "not_found" | "clarification"; citations: CitationRef[]; pending_documents: { id: string; filename: string }[] } }
  | { event: "answer.stopped"; data: { message_id: string } }
  | { event: "answer.failed"; data: { message_id?: string; code: string } };

export async function streamAnswer(cid: string, question: string, onEvent: (e: AnswerEvent) => void, signal?: AbortSignal): Promise<void>;
// Tách khung theo "\n\n", đọc dòng "event:" và "data:", bỏ dòng bắt đầu bằng ":" (keep-alive).
// HTTP != 200 trước khi stream → ném ApiError(code) từ body JSON (dùng chung client.ts).
```

**Chỉ số trích dẫn:** mỗi `answer.delta` mang `text` của một khối và `citations` của khối đó. Hiển thị `text` rồi chèn các nút `[idx]` ngay sau khối. Nút là `<button>` có `aria-label="Nguồn {idx}: {filename} trang {page}"`, mở popover bằng Enter/Space, Esc đóng và trả focus về nút.

**Danh sách "Nguồn"** cuối câu trả lời lấy từ `answer.completed.citations`, gộp theo `idx`: `HopDongKhung.pdf · trang 14`. Trích dẫn có `filename = null` hiển thị "Tài liệu đã được gỡ".

**Trạng thái theo sự kiện kết thúc:**
| Sự kiện | Hiển thị |
|---|---|
| `answer.completed`, `answered` | Nội dung + nguồn + nút sao chép |
| `answer.completed`, `not_found` | "Không tìm thấy thông tin này trong các tài liệu đã tải lên." + 2 gợi ý: diễn đạt lại câu hỏi; kiểm tra tài liệu liên quan đã tải lên và ở trạng thái "Sẵn sàng" (AC-US010-2) |
| `answer.completed`, `clarification` | Nội dung (các đáp án kèm nguồn) |
| `pending_documents` không rỗng | "Tài liệu sau chưa được dùng để trả lời vì đang xử lý: {tên}" (AC-US001-3) |
| `answer.stopped` | Giữ phần đã hiện + nhãn "Đã dừng theo yêu cầu của bạn · câu trả lời chưa đầy đủ" |
| `answer.failed` / mất kết nối | Nhãn "Câu trả lời bị gián đoạn — chưa hoàn tất" + nút "Tạo lại câu trả lời" (gửi lại đúng câu hỏi thành lượt mới). Không có nút sao chép |

**Dừng (US-017):** khi đang stream, nút Gửi thành "Dừng" (đỏ). Bấm → `POST /messages/{message_id}/stop`, ngừng thêm text ngay trên UI (bỏ qua delta đến sau), chờ `answer.stopped`; ô nhập sẵn sàng ngay.

**Ô nhập (US-006):** nút Gửi vô hiệu khi `question.trim() === ""`, khi đang stream, hoặc khi không có tài liệu "Sẵn sàng" (hiện gợi ý tải tài liệu). Giới hạn `question_max_chars` = 2000 ký tự. Lưu bản nháp vào `sessionStorage["cwd_draft"]`; khi API trả 401, chuyển sang trang đăng nhập rồi khôi phục bản nháp sau khi đăng nhập lại (AC-US012-2, cơ chế chung ở T-04).

**Hội thoại (US-016):** lần gửi đầu tiên nếu chưa có `conversationId` thì gọi `POST /doc-sets/{dsid}/conversations`. Nút "Hội thoại mới" ở cuối thanh tài liệu: tạo conversation mới, xóa vùng hội thoại, giữ nguyên danh sách tài liệu.

**Sao chép (US-018):** văn bản thuần:
```
{nội dung câu trả lời, bỏ markdown, chỉ số dạng [1]}

Nguồn:
[1] HopDongKhung.pdf, trang 14
[2] PhuLuc2.pdf, trang 3
```
Dùng `navigator.clipboard.writeText`, sau đó hiện toast "Đã sao chép câu trả lời kèm nguồn. Nhớ đối chiếu nguồn trước khi gửi cho đối tác."

**Mở PDF gốc (US-019):** `window.open('/api/v1/documents/{document_id}/file#page={page}', '_blank', 'noopener')`. Nếu `GET /citations/{id}` trả 410 `DOCUMENT_REMOVED` thì popover hiện "Tài liệu đã được gỡ khỏi bộ tài liệu…" và ẩn nút mở.

**Markdown:** `react-markdown` không bật `rehype-raw`; chỉ cho phép đoạn, danh sách, in đậm, bảng.

## 3. Tiêu chí hoàn thành
- [ ] Cho trước có tài liệu "Sẵn sàng"; khi Lan gõ câu hỏi và nhấn Enter; thì chỉ báo "Đang trả lời…" hiện ngay và nội dung hiện dần (AC-US006-1).
- [ ] Cho trước ô nhập rỗng hoặc chỉ có khoảng trắng; khi nhấn Enter; thì không có request nào được gửi (AC-US006-3).
- [ ] Cho trước câu trả lời có nội dung; khi hiển thị xong; thì có ≥ 1 chỉ số `[n]` và danh sách nguồn gồm tên file và số trang (AC-US009-1).
- [ ] Cho trước một `[n]`; khi bấm; thì popover hiện đoạn trích ≤ 300 ký tự, tên file, số trang (AC-US009-2); nút "Mở tài liệu gốc" mở tab mới đúng trang (AC-US019-1).
- [ ] Cho trước `answer_type = not_found`; khi hiển thị; thì có thông điệp và 2 gợi ý (AC-US010-2).
- [ ] Cho trước đang trả lời; khi bấm "Dừng"; thì nội dung ngừng ≤ 1 s, phần đã hiện được giữ kèm nhãn đã dừng, ô nhập dùng được (AC-US017-1).
- [ ] Cho trước câu trả lời hoàn tất; khi bấm "Sao chép kèm nguồn"; thì clipboard chứa nội dung và danh sách nguồn dạng văn bản thuần (AC-US018-1).
- [ ] Cho trước đang ở giữa hội thoại; khi bấm "Hội thoại mới"; thì vùng hội thoại trống, danh sách tài liệu giữ nguyên (AC-US016-1).
- [ ] Nội dung chứa `<script>` hoặc `<img onerror>` hiển thị dạng chữ, không thực thi.

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| Vitest `sse.test.ts`: chuỗi SSE bị cắt giữa khung, có dòng keep-alive | Parse đúng thứ tự sự kiện |
| Vitest `copy.test.ts`: câu trả lời có markdown + 2 nguồn | Đúng định dạng văn bản thuần ở §2.2 |
| Vitest `AnswerCard`: mỗi loại sự kiện kết thúc | Đúng nhãn/thông điệp theo bảng trạng thái |
| Playwright (với fake LLM của backend): hỏi → stream → bấm `[1]` → popover | Thấy đoạn trích và nút mở tài liệu |
| Playwright: bấm Dừng giữa chừng | Nhãn "Đã dừng…", Composer bật lại |
| Playwright: bàn phím Tab tới `[1]`, Enter, Esc | Popover mở/đóng, focus trả về `[1]` |

## 5. Ghi chú
- Backend không chèn chuỗi `[n]` vào `text`; vị trí chỉ số do frontend dựng từ `citations` của từng delta. T-10 cần giữ đúng quy ước này.
- Không có API đọc lại lịch sử hội thoại: tải lại trang sẽ mở hội thoại trống. Chấp nhận được ở bản thử nghiệm.
- Khi làm: khóa bản nháp dùng chung với T-04 là `sessionStorage["cwd.draft"]`. Chỉ số `[n]` được chèn bằng ký tự đánh dấu vùng riêng (Private Use) rồi thay bằng nút qua một rehype plugin, nên markdown nhiều đoạn vẫn hiển thị đúng. Popover render qua portal (tránh bị cắt bởi vùng cuộn).
