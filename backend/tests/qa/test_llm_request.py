import json
import uuid
from types import SimpleNamespace as NS

from app.config import Settings
from app.qa.llm import LlmClient, RawCitation, TextBlock, build_answer_request, iter_text_blocks
from app.qa.prompts import ANSWER_SYSTEM_PROMPT
from app.qa.retriever import RetrievedChunk

CHUNK = RetrievedChunk(
    chunk_id=uuid.UUID(int=1),
    document_id=uuid.UUID(int=2),
    filename="HopDongKhung.pdf",
    page=14,
    content="Thời hạn thanh toán là 30 ngày. Chậm giao hàng được gia hạn 15 ngày.",
    score=0.03,
)


def test_build_answer_request_snapshot():
    settings = Settings(_env_file=None, llm_model="claude-opus-5-5", llm_max_tokens=4000)
    req = build_answer_request(settings, "Có ngoại lệ không?", [("Thời hạn thanh toán?", "30 ngày")], [CHUNK])
    assert req == {
        "model": "claude-opus-5-5",
        "max_tokens": 4000,
        "output_config": {"effort": "low"},
        "betas": ["server-side-fallback-2026-07-01"],
        "fallbacks": "default",
        "system": [{"type": "text", "text": ANSWER_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        "messages": [
            {"role": "user", "content": "Thời hạn thanh toán?"},
            {"role": "assistant", "content": "30 ngày"},
            {
                "role": "user",
                "content": [
                    {
                        "type": "search_result",
                        "source": f"doc:{uuid.UUID(int=2)}#p=14#c={uuid.UUID(int=1)}",
                        "title": "HopDongKhung.pdf · trang 14",
                        "content": [
                            {
                                "type": "text",
                                "text": "Thời hạn thanh toán là 30 ngày. Chậm giao hàng được gia hạn 15 ngày.",
                            }
                        ],
                        "citations": {"enabled": True},
                    },
                    {"type": "text", "text": "Câu hỏi: Có ngoại lệ không?"},
                ],
            },
        ],
    }
    dumped = json.dumps(req)
    assert '"thinking"' not in dumped and '"temperature"' not in dumped


def test_empty_history_answer_sent_as_marker():
    settings = Settings(_env_file=None)
    req = build_answer_request(settings, "q2", [("q1", "")], [CHUNK])
    assert req["messages"][1] == {"role": "assistant", "content": "[KHONG_TIM_THAY]"}


async def _aiter(items):
    for it in items:
        yield it


async def test_stream_parse_with_fake_events():
    events = [
        NS(type="message_start"),
        NS(type="content_block_start", index=0, content_block=NS(type="thinking", thinking="")),
        NS(type="content_block_stop", index=0),
        NS(type="content_block_start", index=1, content_block=NS(type="text", text="")),
        NS(type="content_block_delta", index=1, delta=NS(type="text_delta", text="Thời hạn ")),
        NS(type="content_block_delta", index=1, delta=NS(type="text_delta", text="là 30 ngày")),
        NS(
            type="content_block_delta",
            index=1,
            delta=NS(
                type="citations_delta",
                citation=NS(type="search_result_location", search_result_index=0, cited_text="30 ngày"),
            ),
        ),
        NS(type="content_block_stop", index=1),
        NS(type="content_block_start", index=2, content_block=NS(type="text", text="")),
        NS(type="content_block_delta", index=2, delta=NS(type="text_delta", text=" nói chung.")),
        NS(type="content_block_stop", index=2),
        NS(type="message_stop"),
    ]
    blocks = [b async for b in iter_text_blocks(_aiter(events))]
    assert blocks == [
        TextBlock("Thời hạn là 30 ngày", (RawCitation(0, "30 ngày"),)),
        TextBlock(" nói chung.", ()),
    ]


async def test_rewrite_falls_back_on_error():
    class Boom:
        def with_options(self, **_):
            return self

        @property
        def messages(self):
            return self

        async def create(self, **_):
            raise RuntimeError("mất mạng")

    llm = LlmClient(Settings(_env_file=None, anthropic_api_key="test"))
    llm.client = Boom()
    assert await llm.rewrite_question([("q1", "a1")], "Điều khoản đó?") == "Điều khoản đó?"


async def test_rewrite_without_history_returns_question():
    llm = LlmClient(Settings(_env_file=None, anthropic_api_key="test"))
    assert await llm.rewrite_question([], "Câu hỏi đầu") == "Câu hỏi đầu"
