"""Chạy thử với Claude thật: `python -m app.qa.llm_smoke` (cần ANTHROPIC_API_KEY).

Hỏi 1 câu trên 2 đoạn mẫu, in từng text block kèm trích dẫn search_result_location.
"""

import asyncio
import uuid

from app.config import get_settings
from app.qa.citation_filter import CitationFilter, SourceRef
from app.qa.llm import AnswerDone, LlmClient
from app.qa.retriever import RetrievedChunk

SAMPLE = [
    RetrievedChunk(
        uuid.uuid4(), uuid.uuid4(), "HopDongKhung.pdf", 14,
        "Điều 5. Thời hạn thanh toán là 30 ngày kể từ ngày nhận hóa đơn hợp lệ.", 0.03,
    ),
    RetrievedChunk(
        uuid.uuid4(), uuid.uuid4(), "PhuLuc2.pdf", 3,
        "Trường hợp chậm giao hàng, thời hạn thanh toán được gia hạn thêm 15 ngày.", 0.02,
    ),
]


async def main() -> None:
    llm = LlmClient(get_settings())
    filt = CitationFilter([SourceRef(c.chunk_id, c.document_id, c.filename, c.page) for c in SAMPLE])
    async for ev in llm.stream_answer("Thời hạn thanh toán là bao lâu và có ngoại lệ không?", [], SAMPLE):
        if isinstance(ev, AnswerDone):
            print(f"\n[stop_reason={ev.stop_reason} in={ev.input_tokens} out={ev.output_tokens}]")
            break
        print(f"BLOCK {ev.text!r} citations={[(c.search_result_index, c.cited_text[:40]) for c in ev.citations]}")
        for span in filt.accept(ev):
            print(f"  → hiển thị: {span.text!r} {[c.idx for c in span.citations]}")
    result = filt.finalize()
    print(f"answer_type={result.answer_type}, {len(result.citations)} trích dẫn")


if __name__ == "__main__":
    asyncio.run(main())
