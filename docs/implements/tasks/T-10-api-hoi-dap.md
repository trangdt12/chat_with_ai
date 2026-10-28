# T-10 · API hỏi đáp streaming, câu hỏi tiếp nối, dừng, trích dẫn

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-001 (AC-2, AC-3), US-006 (AC-1, AC-3), US-007, US-008, US-009 (AC-1, AC-2), US-010, US-011 (AC-1), US-014 (AC-1), US-016 (AC-1), US-017 (AC-1) | T-08, T-09 | 2,5 ngày |

## 1. Mục tiêu
Ghép tìm kiếm (T-08) và Claude + CitationFilter (T-09) thành API hỏi đáp mà FE (T-11) dùng: tạo hội thoại, gửi câu hỏi và nhận câu trả lời qua **SSE**, dừng câu trả lời đang tạo, xem đoạn trích của một trích dẫn. Mỗi lượt hỏi đáp được lưu vào `turns` và `citations`.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/qa/router.py` | 4 endpoint ở §2.2 |
| `backend/app/qa/service.py` | `create_conversation`, `prepare_question`, `run_answer` (async generator sự kiện), `get_citation` |
| `backend/app/qa/streams.py` | `StreamRegistry`: `dict[UUID, ActiveStream]` trong bộ nhớ, dùng để dừng |
| `backend/app/qa/schemas.py` | `QuestionIn`, các payload sự kiện SSE, `CitationDetailOut` |
| `backend/tests/qa/test_ask_api.py` | Integration với `FakeLlmClient` + `FakeEmbedder` |

### 2.2 Chi tiết

**`POST /doc-sets/{dsid}/conversations`** (member, manager) → 201 `{"conversation_id": "uuid"}`. Nút "Hội thoại mới" (US-016) chỉ gọi endpoint này; danh sách tài liệu không đổi.

**`POST /conversations/{cid}/messages`**, body `{"question": "..."}` → `text/event-stream`.

Các kiểm tra trước khi mở stream (lỗi trả JSON thường, không qua SSE):

| # | Điều kiện | Lỗi |
|---|---|---|
| 1 | Chưa đăng nhập | 401 `UNAUTHENTICATED` |
| 2 | Hội thoại không tồn tại hoặc không thuộc người gọi | 404 `NOT_FOUND` |
| 3 | Người gọi không còn là member/manager của `doc_set` (đọc DB mỗi request) | 403 `FORBIDDEN` (AC-US014-1) |
| 4 | `question.strip()` rỗng hoặc dài hơn `question_max_chars` | 422 `VALIDATION_ERROR` (AC-US006-3) |
| 5 | Bộ không có tài liệu `ready` nào | 409 `NO_READY_DOCUMENTS` |

**Luồng `run_answer`** (sự kiện SSE theo đúng thứ tự):

```text
message_id = uuid4(); registry.add(message_id, user_id, cancel=asyncio.Event())
→ event: answer.started   {message_id, turn_index}
history  = ≤ history_turns lượt completed gần nhất của hội thoại (question, answer)
query    = question nếu turn_index == 0, ngược lại await llm.rewrite_question(history, question)   # US-011
pending  = documents của bộ có status IN ('uploaded','processing') → [{id, filename}]           # AC-US001-3
result   = await retrieve(db, embedder, dsid, query)
if result.not_found:                     # không gọi Claude
    → answer.completed {message_id, answer_type:"not_found", citations:[], pending_documents}
else:
    filt = CitationFilter([SourceRef(...) for c in result.chunks])
    agen = llm.stream_answer(question, history, result.chunks)
    async for ev in agen:
        if cancel.is_set(): await agen.aclose(); → answer.stopped {message_id}; lưu status=stopped; return
        if TextBlock: for span in filt.accept(ev): → answer.delta {text: span.text, citations: [...]}
        if AnswerDone:
            end_turn   → out = filt.finalize(); gửi out.late_spans dạng answer.delta;
                         → answer.completed {message_id, answer_type: out.answer_type, citations: out.citations, pending_documents}
            max_tokens → answer.failed {message_id, code:"MAX_TOKENS"}
            refusal    → answer.failed {message_id, code:"AI_REFUSED"}
finally: registry.remove(message_id)
```

Câu hỏi gửi cho Claude là **câu gốc**, còn câu đã viết lại chỉ dùng để tìm kiếm. Claude vẫn thấy lịch sử, nên hiểu được đại từ tham chiếu.

**Payload** (khớp kiểu `SseEvent` ở T-11):
```json
answer.delta     {"text": "Thời hạn thanh toán là 30 ngày", "citations": [{"idx": 1, "citation_id": "uuid", "document_id": "uuid", "filename": "HopDongKhung.pdf", "page": 14}]}
answer.completed {"message_id": "uuid", "answer_type": "answered", "citations": [ ...như trên, đủ mọi idx... ], "pending_documents": [{"id": "uuid", "filename": "BaoGia_v3.pdf"}]}
answer.failed    {"message_id": "uuid", "code": "AI_UNAVAILABLE"}
```

**Ánh xạ lỗi trong stream:**
- `anthropic.APIConnectionError`, `RateLimitError`, `APIStatusError` (5xx, 529) → `AI_UNAVAILABLE`.
- `APITimeoutError` → `AI_TIMEOUT`.
- Lỗi khác → `INTERNAL`.
- Mọi trường hợp: lưu `status=incomplete` với phần đã gửi, rồi gửi `answer.failed`.

**Người dùng đóng tab:** kiểm tra `await request.is_disconnected()` giữa các block. Nếu đã ngắt thì `aclose()` và lưu `incomplete`.

**Keep-alive:** cứ 15 giây không có sự kiện thì gửi comment `: keep-alive`. Dùng `sse-starlette` (`EventSourceResponse`, `ping=15`) hoặc `StreamingResponse` tự định dạng `event:`/`data:`.

**Lưu kết quả** (một transaction, sau khi stream kết thúc, kể cả khi dừng hay lỗi):

| Kết cục | `turns.status` | `answer_type` | `answer` | `citations` |
|---|---|---|---|---|
| `completed` | `completed` | theo `FilterResult` | `answer_text` | `FilterResult.citations` |
| Dừng | `stopped` | `answered` nếu đã có citation, ngược lại `not_found` | text từ `filt.snapshot()` | từ `snapshot()` |
| Lỗi / mất kết nối | `incomplete` | như trên | như trên | như trên |

- `turns.id = message_id`; `turn_index` = số lượt hiện có trong hội thoại.
- Insert `citations(id=citation_id, turn_id, idx, document_id, chunk_id, filename, page, snippet)` khớp với id đã gửi trong SSE.
- Ghi audit `query` với `meta={"answer_type": ..., "status": ..., "citation_count": n}`. **Không** ghi câu hỏi hay câu trả lời.

**`POST /messages/{mid}/stop`** (chủ hội thoại):

```python
@dataclass
class ActiveStream: user_id: UUID; cancel: asyncio.Event

def stop(mid, user) -> None:
    s = registry.get(mid)
    if s and s.user_id == user.id: s.cancel.set()
    # trả 202 cả khi không tìm thấy (stream đã kết thúc) — idempotent, không lộ thông tin
```
Stream kiểm tra `cancel` sau mỗi block. Ngoài ra, một task song song đợi `cancel.wait()` rồi gọi `agen.aclose()`, để dừng trong ≤ 1 giây kể cả khi Claude đang "nghĩ" (chưa ra block nào). Bản thử nghiệm chạy một tiến trình `api` (uvicorn `--workers 1`), nên registry trong bộ nhớ là đủ.

**`GET /citations/{id}`** (member, manager của bộ chứa hội thoại): trả `{"document_id", "filename", "page", "snippet"}` và ghi audit `view_citation`. Nếu `citations.removed = true` → 410 `DOCUMENT_REMOVED`. Admin hoặc người ngoài nhóm → 403 (AC-US013-2).

## 3. Tiêu chí hoàn thành
- [ ] Cho trước có tài liệu "Sẵn sàng", khi gửi câu hỏi, thì SSE trả `answer.started` → ≥ 1 `answer.delta` có trích dẫn → `answer.completed` (AC-US006-1, AC-US009-1).
- [ ] Cho trước câu hỏi về nội dung chỉ có trong file X, thì trích dẫn trỏ tới X (AC-US001-2).
- [ ] Cho trước có 1 file "Đang xử lý", thì `answer.completed.pending_documents` chứa tên file đó (AC-US001-3).
- [ ] Cho trước câu hỏi ngoài tài liệu, thì `answer_type = not_found` (AC-US007-2, AC-US010-1).
- [ ] Cho trước lượt 1 "Thời hạn thanh toán trong hợp đồng khung là bao lâu?", khi hỏi tiếp "Điều khoản đó có ngoại lệ không?", thì lượt 2 tìm và trả lời về điều khoản thanh toán (AC-US011-1).
- [ ] Cho trước người dùng bấm "Hội thoại mới" rồi hỏi một câu chỉ có đại từ, thì câu trả lời không dùng ngữ cảnh cũ (AC-US016-1).
- [ ] Cho trước câu trả lời đang stream, khi gọi `stop`, thì stream kết thúc bằng `answer.stopped` trong ≤ 1 giây và lượt được lưu `stopped` với phần đã hiện (AC-US017-1).
- [ ] Câu hỏi rỗng → 422; người ngoài nhóm → 403, không có nội dung nào trả về (AC-US006-3, AC-US014-1).
- [ ] `GET /citations/{id}` trả đoạn trích ≤ 300 ký tự kèm tên file, trang (AC-US009-2).
- [ ] Log và audit không chứa câu hỏi, câu trả lời, đoạn trích.

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `test_ask_happy_path_event_order` | started → delta+ → completed; turn + citations lưu đúng, `citation_id` khớp SSE |
| `test_ask_not_found_skips_llm` | Retriever `not_found` → FakeLlm không được gọi |
| `test_ask_pending_documents` | Có tài liệu `processing` → có trong `pending_documents` |
| `test_ask_followup_uses_rewrite` | `turn_index=1` → `rewrite_question` được gọi, retriever nhận câu đã viết lại |
| `test_new_conversation_no_history` | Hội thoại mới → `history` rỗng |
| `test_ask_validation_and_permissions` | Rỗng → 422; ngoài nhóm → 403; không có tài liệu ready → 409 |
| `test_stop_mid_stream` | FakeLlm chậm; gọi stop → `answer.stopped` ≤ 1 s, status `stopped` |
| `test_stop_other_user_ignored` | Người khác gọi stop → stream vẫn chạy |
| `test_llm_error_mid_stream` | FakeLlm ném `APIConnectionError` sau 1 block → `answer.failed AI_UNAVAILABLE`, status `incomplete` |
| `test_max_tokens_is_failed` | `AnswerDone(max_tokens)` → `answer.failed MAX_TOKENS` |
| `test_get_citation_ok_removed_forbidden` | 200 / 410 / 403 |
| `test_no_content_in_audit_meta` | `meta` không có khóa `question`, `answer`, `snippet` |

## 5. Ghi chú
- Tham khảo luồng ở [SAD §3.2.1](../../design/SAD.md) và sự kiện ở SAD Phụ lục A.4 (đã bỏ `schema_version` và `latency` cho gọn).
- Nếu sau này chạy nhiều worker uvicorn, registry trong bộ nhớ không còn đủ; khi đó chuyển sang PostgreSQL `LISTEN/NOTIFY` như thiết kế gốc (Blueprint DD-08).
- Khi làm: lượt được lưu **trước** khi gửi sự kiện kết thúc (completed/stopped/failed) để test và FE đọc được ngay. Dừng dùng `asyncio.wait` giữa `__anext__` và `cancel.wait()`, hủy task đang chờ để thoát `async with` của SDK.
