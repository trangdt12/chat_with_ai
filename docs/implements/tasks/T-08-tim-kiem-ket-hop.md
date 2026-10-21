# T-08 · Tìm kiếm kết hợp vector + từ khóa

| Story | Phụ thuộc | Ước lượng |
|---|---|---|
| US-007 (AC-1, AC-2), US-008 (AC-1), US-010 (AC-1), US-002 (AC-3) | T-06 | 1,5 ngày |

## 1. Mục tiêu
Với một câu hỏi, tìm tối đa 10 đoạn văn liên quan nhất trong bộ tài liệu, chỉ trong các tài liệu `ready`. Hai cách tìm được kết hợp: vector (hiểu nghĩa, hỏi chéo Việt/Anh) và từ khóa (mã số, tên riêng, số hợp đồng). Nếu không có gì đủ liên quan, trả cờ "không tìm thấy" để T-10 trả lời ngay mà không gọi Claude.

## 2. Việc cần làm
### 2.1 File
| File | Nội dung |
|---|---|
| `backend/app/qa/retriever.py` | `RetrievedChunk`, `RetrievalResult`, `retrieve()`, `rrf_merge()` |
| `backend/tests/qa/test_retriever.py` | Unit (RRF, giới hạn theo tài liệu) + integration (Postgres thật) |

### 2.2 Chi tiết

```python
@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    filename: str
    page: int
    content: str
    score: float            # điểm RRF

@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[RetrievedChunk]   # ≤ retrieval_top_k, thứ tự = search_result_index gửi cho Claude
    max_cos: float                 # cosine cao nhất của nhánh vector (0 nếu rỗng)
    fts_hits: int                  # số kết quả nhánh từ khóa
    not_found: bool                # max_cos < τ và fts_hits == 0

async def retrieve(db: AsyncSession, embedder: Embedder, doc_set_id: UUID, query: str) -> RetrievalResult: ...
```

**Nhánh vector:**
```sql
SET LOCAL hnsw.ef_search = 80;
SELECT c.id, c.document_id, d.filename, c.page_number, c.content,
       1 - (c.embedding <=> CAST(:qvec AS vector)) AS cos
FROM chunks c JOIN documents d ON d.id = c.document_id
WHERE c.doc_set_id = :ds AND d.status = 'ready'
ORDER BY c.embedding <=> CAST(:qvec AS vector)
LIMIT :k;                                         -- retrieval_top_k_branch = 30
```

**Nhánh từ khóa:**
```sql
SELECT c.id, c.document_id, d.filename, c.page_number, c.content,
       ts_rank_cd(c.tsv, q) AS r
FROM chunks c JOIN documents d ON d.id = c.document_id,
     websearch_to_tsquery('simple', f_unaccent(:q)) q
WHERE c.doc_set_id = :ds AND d.status = 'ready' AND c.tsv @@ q
ORDER BY r DESC
LIMIT :k;
```

- `qvec = embedder.embed_query(query)`, gọi qua `asyncio.to_thread`. Hai truy vấn chạy tuần tự trên cùng session là đủ nhanh ở quy mô này.
- `f_unaccent` là hàm IMMUTABLE bọc `unaccent` do T-02 tạo. Cột `tsv` cũng dùng hàm này, nên "hop dong" khớp "hợp đồng".

**Hợp nhất (RRF, k = 60) và đa dạng nguồn:**
```text
rrf[id] = Σ_nhánh 1 / (60 + rank_nhánh(id))          # rank tính từ 1
ranked  = sắp xếp giảm dần theo rrf; hòa điểm thì theo chunk_id cho tất định
picked  = []; per_doc = {}
for c in ranked:
    if per_doc.get(c.document_id, 0) < retrieval_max_per_doc (4): picked.append(c); per_doc[...] += 1
    if len(picked) == retrieval_top_k (10): break
not_found = (max_cos < retrieval_not_found_tau) and fts_hits == 0
```
`rrf_merge` là hàm thuần (không DB) để unit test dễ.

**Ngưỡng τ:** mặc định 0,35 (config). Hiệu chỉnh ở T-15: chạy bộ câu hỏi, chọn τ lớn nhất sao cho ≤ 2% câu có đáp án bị chặn nhầm. Nếu không chọn được, đặt τ = 0 (tắt chặn sớm, để Claude tự trả `[KHONG_TIM_THAY]`).

## 3. Tiêu chí hoàn thành
- [ ] Cho trước bộ có tài liệu `ready` và một tài liệu `processing`, khi tìm kiếm, thì không bao giờ trả đoạn văn của tài liệu `processing` (AC-US001-3).
- [ ] Cho trước câu hỏi chứa mã số hợp đồng chỉ có trong một tài liệu, khi tìm kiếm, thì đoạn chứa mã đó nằm trong kết quả nhờ nhánh từ khóa.
- [ ] Cho trước câu hỏi tiếng Anh về nội dung tài liệu tiếng Việt, khi tìm kiếm, thì có đoạn liên quan trong top 10 (NFR-004).
- [ ] Cho trước 10 đoạn hàng đầu đều thuộc 1 tài liệu, khi hợp nhất, thì tối đa 4 đoạn thuộc tài liệu đó (US-008).
- [ ] Cho trước câu hỏi không liên quan ("Thủ đô của Pháp là gì?"), khi tìm kiếm, thì `not_found = True` (AC-US007-2, AC-US010-1).
- [ ] Chỉ trả đoạn văn của `doc_set_id` được truyền vào.
- [ ] Thời gian `retrieve` < 500 ms với bộ 50 file trên máy dev (không tính lần tải model đầu tiên).

## 4. Kiểm thử
| Test | Kỳ vọng |
|---|---|
| `test_rrf_merge_order` | Đoạn đứng đầu cả 2 nhánh xếp đầu; công thức đúng với k = 60 |
| `test_rrf_max_per_doc` | 12 ứng viên cùng tài liệu + 3 tài liệu khác → 4 + 3 |
| `test_rrf_tie_deterministic` | Chạy 2 lần cho cùng thứ tự |
| `test_not_found_flag` | `max_cos=0.2, fts_hits=0` → True; `fts_hits=1` → False |
| `test_retrieve_excludes_non_ready` (integration, `FakeEmbedder`) | Không có chunk của tài liệu `processing`/`failed` |
| `test_retrieve_scoped_to_doc_set` | Chunk của bộ khác không xuất hiện |
| `test_fts_unaccent` | Truy vấn "hop dong khung" khớp đoạn "Hợp đồng khung" |

## 5. Ghi chú
- Tham khảo Blueprint ALG-03, DD-04, DD-05 ([Blueprint_SDD.md §3.8](../../design/Blueprint_SDD.md)).
- Nếu chất lượng tìm kiếm tiếng Việt chưa đạt (đo ở T-15), các nút chỉnh đều nằm trong config: `retrieval_top_k`, `retrieval_max_per_doc`, `chunk_max_chars`, τ.
