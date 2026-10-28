"""ALG-05: quyết định khối văn bản nào được hiện cho người dùng.

Khối có nguồn hiện ngay; câu không có nguồn bị loại (trừ câu nối nằm giữa hai khối có nguồn);
nhận diện "không tìm thấy" và "cần làm rõ". Không span nào đã gửi bị rút lại. Python thuần.
"""

import re
import uuid
from dataclasses import dataclass

from app.qa.llm import TextBlock
from app.qa.prompts import CLARIFY_MARKER, NOT_FOUND_MARKER

SNIPPET_MAX = 300
_CONNECTIVE_MAX_WORDS = 12
_CAPITALIZED_RATIO = 0.3


@dataclass(frozen=True)
class SourceRef:  # phần tử i ↔ search_result_index i
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int


@dataclass(frozen=True)
class CitationOut:
    idx: int
    citation_id: uuid.UUID
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    page: int
    snippet: str  # ≤ 300


@dataclass(frozen=True)
class Span:
    text: str
    citations: tuple[CitationOut, ...]  # rỗng với câu nối


@dataclass(frozen=True)
class FilterResult:
    answer_type: str  # answered | not_found | clarification
    late_spans: tuple[Span, ...]  # chỉ dùng cho ca làm rõ không có nguồn
    answer_text: str  # text đã/sẽ hiển thị; "" nếu not_found
    citations: tuple[CitationOut, ...]


def is_connective(text: str) -> bool:
    """Câu nối ngắn không mang thông tin ("Ngoài ra, ", "\\n- ") thì được giữ giữa hai khối có nguồn."""
    if not text.strip():
        return True
    if re.search(r"\d", text):
        return False
    words = re.findall(r"\w+", text)
    if len(words) > _CONNECTIVE_MAX_WORDS:
        return False
    # Nhiều từ viết hoa (tên riêng) gợi ý câu có thông tin; không tính từ đầu câu.
    counted = [w for sentence in re.split(r"[.!?…]\s+", text) for w in re.findall(r"\w+", sentence)[1:]]
    if counted and sum(w[0].isupper() for w in counted) / len(counted) >= _CAPITALIZED_RATIO:
        return False
    return True


class CitationFilter:
    def __init__(self, sources: list[SourceRef]):
        self._sources = sources
        self._by_chunk: dict[uuid.UUID, CitationOut] = {}
        self._held: list[str] = []
        self._emitted: list[Span] = []
        self._not_found = False
        self._clarify = False
        self._seen_text = False

    def _map(self, block: TextBlock) -> tuple[CitationOut, ...]:
        out: list[CitationOut] = []
        for raw in block.citations:
            if not 0 <= raw.search_result_index < len(self._sources):
                continue  # index ngoài phạm vi → bỏ
            src = self._sources[raw.search_result_index]
            cit = self._by_chunk.get(src.chunk_id)
            if cit is None:
                cit = CitationOut(
                    idx=len(self._by_chunk) + 1,
                    citation_id=uuid.uuid4(),
                    chunk_id=src.chunk_id,
                    document_id=src.document_id,
                    filename=src.filename,
                    page=src.page,
                    snippet=raw.cited_text[:SNIPPET_MAX],
                )
                self._by_chunk[src.chunk_id] = cit
            if cit not in out:
                out.append(cit)
        return tuple(out)

    def accept(self, block: TextBlock) -> list[Span]:
        """Trả các span cần gửi NGAY cho người dùng."""
        if self._not_found:
            return []
        if NOT_FOUND_MARKER in block.text:
            # Đã hiện nội dung có nguồn thì không rút lại được: chỉ bỏ khối chứa marker.
            if not self._emitted:
                self._not_found = True
            return []

        text = block.text
        if not self._seen_text and text.strip():
            self._seen_text = True
            stripped = text.lstrip()
            if stripped.startswith(CLARIFY_MARKER):
                self._clarify = True
                text = stripped[len(CLARIFY_MARKER) :].lstrip()

        citations = self._map(block) if block.citations else ()
        if not citations:
            if text:
                self._held.append(text)
            return []

        spans: list[Span] = []
        if self._emitted:  # khối giữ lại nằm giữa hai khối có nguồn: chỉ giữ câu nối
            spans.extend(Span(t, ()) for t in self._held if is_connective(t))
        self._held = []  # khối nằm trước khối có nguồn đầu tiên luôn bị loại
        spans.append(Span(text, citations))
        self._emitted.extend(spans)
        return spans

    def finalize(self) -> FilterResult:
        """Gọi 1 lần khi stop_reason == end_turn."""
        if self._not_found:
            return FilterResult("not_found", (), "", ())
        if not self._by_chunk:
            if self._clarify:
                late = tuple(Span(t, ()) for t in self._held if t.strip())
                self._emitted.extend(late)
                self._held = []
                return FilterResult("clarification", late, "".join(s.text for s in late), ())
            return FilterResult("not_found", (), "", ())  # AC-US009-4: không câu nào có nguồn
        self._held = []  # khối không nguồn ở cuối bị loại
        text, citations = self.snapshot()
        return FilterResult("clarification" if self._clarify else "answered", (), text, citations)

    def snapshot(self) -> tuple[str, tuple[CitationOut, ...]]:
        """Phần đã gửi cho người dùng — dùng khi dừng / lỗi."""
        return "".join(s.text for s in self._emitted), tuple(self._by_chunk.values())
