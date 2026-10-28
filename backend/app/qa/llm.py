"""Gọi Claude với search_result blocks có citations; trả từng text block kèm trích dẫn khi block đóng."""

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Protocol

from app.config import Settings, get_settings
from app.ingestion.chunker import split_blocks
from app.qa.prompts import ANSWER_SYSTEM_PROMPT, NOT_FOUND_MARKER, REWRITE_SYSTEM_PROMPT

if TYPE_CHECKING:
    from app.qa.retriever import RetrievedChunk

log = logging.getLogger(__name__)

FALLBACK_BETA = "server-side-fallback-2026-07-01"
SEARCH_BLOCK_MAX_CHARS = 300
REWRITE_TIMEOUT_SECONDS = 8
REWRITE_MAX_TOKENS = 1000


@dataclass(frozen=True)
class RawCitation:
    search_result_index: int  # 0-based, theo thứ tự search_result trong request
    cited_text: str


@dataclass(frozen=True)
class TextBlock:
    text: str
    citations: tuple[RawCitation, ...]


@dataclass(frozen=True)
class AnswerDone:
    stop_reason: str  # end_turn | max_tokens | refusal | ...
    input_tokens: int
    output_tokens: int


History = Sequence[tuple[str, str]]  # (câu hỏi, câu trả lời) của các lượt trước


class LlmProtocol(Protocol):
    def stream_answer(
        self, question: str, history: History, sources: "Sequence[RetrievedChunk]"
    ) -> AsyncIterator[TextBlock | AnswerDone]: ...

    async def rewrite_question(self, history: History, question: str) -> str: ...


def _history_messages(history: History) -> list[dict]:
    messages: list[dict] = []
    for q, a in history:
        # Lịch sử chỉ gửi text thuần (không gửi lại citations) nên search_result_index khớp đúng `sources`.
        messages.append({"role": "user", "content": q})
        messages.append({"role": "assistant", "content": a or NOT_FOUND_MARKER})
    return messages


def build_answer_request(
    settings: Settings, question: str, history: History, sources: "Sequence[RetrievedChunk]"
) -> dict[str, Any]:
    """Request cho client.beta.messages.stream — hàm thuần để snapshot test."""
    search_results = [
        {
            "type": "search_result",
            "source": f"doc:{c.document_id}#p={c.page}#c={c.chunk_id}",
            "title": f"{c.filename} · trang {c.page}",
            "content": [{"type": "text", "text": b} for b in split_blocks(c.content, SEARCH_BLOCK_MAX_CHARS)],
            "citations": {"enabled": True},
        }
        for c in sources
    ]
    return {
        "model": settings.llm_model,
        "max_tokens": settings.llm_max_tokens,
        # Opus 5.5 luôn có thinking (mặc định effort "medium"); KHÔNG gửi "thinking" hay "temperature".
        "output_config": {"effort": "low"},
        # Bị bộ lọc an toàn từ chối thì server tự chạy lại trên model dự phòng trong cùng lần gọi.
        "betas": [FALLBACK_BETA],
        "fallbacks": "default",
        "system": [{"type": "text", "text": ANSWER_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [
            *_history_messages(history),
            {"role": "user", "content": [*search_results, {"type": "text", "text": f"Câu hỏi: {question}"}]},
        ],
    }


async def iter_text_blocks(events: AsyncIterator[Any]) -> AsyncIterator[TextBlock]:
    """Gom sự kiện stream thành TextBlock. Chỉ yield khi block đóng vì citations có thể đến sau text."""
    buffers: dict[int, tuple[list[str], list[RawCitation]]] = {}
    async for event in events:
        if event.type == "content_block_start":
            # Bỏ qua block thinking / fallback / ...
            if event.content_block.type == "text":
                buffers[event.index] = ([getattr(event.content_block, "text", "") or ""], [])
        elif event.type == "content_block_delta":
            buf = buffers.get(event.index)
            if buf is None:
                continue
            delta = event.delta
            if delta.type == "text_delta":
                buf[0].append(delta.text)
            elif delta.type == "citations_delta" and delta.citation.type == "search_result_location":
                buf[1].append(RawCitation(delta.citation.search_result_index, delta.citation.cited_text))
        elif event.type == "content_block_stop":
            buf = buffers.pop(event.index, None)
            if buf is not None:
                yield TextBlock("".join(buf[0]), tuple(buf[1]))


class LlmClient:
    def __init__(self, settings: Settings):
        import anthropic

        self.settings = settings
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key or None, max_retries=2, timeout=60)

    async def stream_answer(
        self, question: str, history: History, sources: "Sequence[RetrievedChunk]"
    ) -> AsyncIterator[TextBlock | AnswerDone]:
        """Người gọi dừng sớm bằng `await agen.aclose()`: thoát `async with`, SDK đóng kết nối HTTP.

        Exception của SDK (APIConnectionError, RateLimitError, APIStatusError, APITimeoutError) bay ra ngoài.
        """
        req = build_answer_request(self.settings, question, history, sources)
        fallbacks = req.pop("fallbacks")
        async with self.client.beta.messages.stream(**req, extra_body={"fallbacks": fallbacks}) as stream:
            async for block in iter_text_blocks(stream):
                yield block
            msg = await stream.get_final_message()
        yield AnswerDone(msg.stop_reason or "", msg.usage.input_tokens, msg.usage.output_tokens)

    async def rewrite_question(self, history: History, question: str) -> str:
        """Viết lại câu hỏi tiếp nối thành câu độc lập (US-011). Mọi lỗi → trả nguyên câu gốc, không ném lỗi."""
        if not history:
            return question
        try:
            msg = await self.client.with_options(timeout=REWRITE_TIMEOUT_SECONDS, max_retries=0).messages.create(
                model=self.settings.llm_model,
                max_tokens=REWRITE_MAX_TOKENS,
                output_config={"effort": "low"},
                system=REWRITE_SYSTEM_PROMPT,
                messages=[*_history_messages(history), {"role": "user", "content": question}],
            )
        except Exception as e:
            log.warning("rewrite_question lỗi %s — dùng câu gốc", type(e).__name__)
            return question
        if msg.stop_reason == "refusal":
            return question
        text = "".join(b.text for b in msg.content if b.type == "text").strip()
        return text or question


class FakeLlmClient:
    """LLM giả cho pytest và e2e (LLM_FAKE=1), không gọi API.

    Mặc định: câu hỏi chứa "không có" → [KHONG_TIM_THAY]; chứa "tóm tắt" → 30 khối (để thử nút Dừng);
    còn lại trả 2 khối văn bản, mỗi khối trích dẫn search result đầu tiên, `sleep(delay)` giữa các khối.
    Test có thể truyền `script` (danh sách TextBlock / AnswerDone / Exception) để điều khiển từng bước.
    """

    def __init__(self, script: list | None = None, delay: float = 0.2):
        self.script = script
        self.delay = delay
        self.answer_calls: list[dict] = []
        self.rewrite_calls: list[tuple[list, str]] = []

    async def stream_answer(
        self, question: str, history: History, sources: "Sequence[RetrievedChunk]"
    ) -> AsyncIterator[TextBlock | AnswerDone]:
        self.answer_calls.append({"question": question, "history": list(history), "sources": list(sources)})
        for i, step in enumerate(self.script if self.script is not None else self._default(question, sources)):
            if i:
                await asyncio.sleep(self.delay)
            if isinstance(step, BaseException):
                raise step
            yield step

    @staticmethod
    def _default(question: str, sources: "Sequence[RetrievedChunk]") -> list:
        if "không có" in question.lower() or not sources:
            return [TextBlock(NOT_FOUND_MARKER, ()), AnswerDone("end_turn", 10, 5)]
        first = split_blocks(sources[0].content, SEARCH_BLOCK_MAX_CHARS)[0]
        cite = (RawCitation(0, first),)
        if "tóm tắt" in question.lower():  # câu trả lời dài để thử nút Dừng (e2e, demo)
            parts = [TextBlock(f"Ý {i}: {first} ", cite) for i in range(1, 31)]
            return [*parts, AnswerDone("end_turn", 100, 400)]
        return [
            TextBlock(f"Theo tài liệu {sources[0].filename}, {first}", cite),
            TextBlock(" Thông tin này nằm ở trang " + str(sources[0].page) + " của tài liệu.", cite),
            AnswerDone("end_turn", 100, 40),
        ]

    async def rewrite_question(self, history: History, question: str) -> str:
        self.rewrite_calls.append((list(history), question))
        if not history:
            return question
        return f"{history[-1][0]} {question}"


@lru_cache
def get_llm() -> LlmProtocol:
    settings = get_settings()
    return FakeLlmClient() if settings.llm_fake else LlmClient(settings)
