"""Hỏi đáp: tạo hội thoại, chuẩn bị câu hỏi, chạy câu trả lời (sự kiện SSE), xem trích dẫn, đánh giá.

Log và audit KHÔNG chứa câu hỏi, câu trả lời hay đoạn trích (README §2.7).
"""

import asyncio
import contextlib
import json
import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import record_audit
from app.auth.deps import ensure_member, forbidden
from app.auth.policy import AccessContext
from app.config import get_settings
from app.db import SessionLocal
from app.errors import AppError
from app.ingestion.embeddings import EmbedderProtocol
from app.models import Citation, Conversation, Document, Feedback, Turn
from app.qa.citation_filter import CitationFilter, CitationOut, FilterResult, SourceRef, Span
from app.qa.llm import AnswerDone, LlmProtocol, TextBlock
from app.qa.retriever import retrieve
from app.qa.schemas import CitationDetailOut, FeedbackIn, FeedbackOut
from app.qa.streams import StreamRegistry

log = logging.getLogger(__name__)


def not_found() -> AppError:
    return AppError("NOT_FOUND", 404, "Không tìm thấy")


# ---------------------------------------------------------------- hội thoại


async def create_conversation(db: AsyncSession, ctx: AccessContext, dsid: uuid.UUID) -> uuid.UUID:
    ensure_member(ctx, dsid)
    conv = Conversation(user_id=ctx.user_id, doc_set_id=dsid)
    db.add(conv)
    await db.commit()
    return conv.id


@dataclass(frozen=True)
class PreparedQuestion:
    conversation_id: uuid.UUID
    doc_set_id: uuid.UUID
    user_id: uuid.UUID
    turn_index: int
    question: str
    history: list[tuple[str, str]]  # ≤ history_turns lượt completed gần nhất, cũ → mới


async def prepare_question(
    db: AsyncSession, ctx: AccessContext, conversation_id: uuid.UUID, question: str
) -> PreparedQuestion:
    """Các kiểm tra trước khi mở stream; lỗi trả JSON thường, không qua SSE."""
    settings = get_settings()
    conv = await db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != ctx.user_id:
        raise not_found()
    ensure_member(ctx, conv.doc_set_id)  # quyền đọc lại từ DB ở mỗi request (AC-US014-1)

    question = question.strip()
    if not question or len(question) > settings.question_max_chars:
        raise AppError(
            "VALIDATION_ERROR", 422, f"Câu hỏi phải có từ 1 đến {settings.question_max_chars} ký tự"
        )

    ready = await db.scalar(
        select(func.count())
        .select_from(Document)
        .where(Document.doc_set_id == conv.doc_set_id, Document.status == "ready")
    )
    if not ready:
        raise AppError("NO_READY_DOCUMENTS", 409, "Bộ tài liệu chưa có tài liệu nào sẵn sàng")

    turn_index = await db.scalar(
        select(func.count()).select_from(Turn).where(Turn.conversation_id == conversation_id)
    )
    rows = await db.execute(
        select(Turn.question, Turn.answer)
        .where(Turn.conversation_id == conversation_id, Turn.status == "completed")
        .order_by(Turn.turn_index.desc())
        .limit(settings.history_turns)
    )
    history = [(q, a) for q, a in rows.all()][::-1]
    await db.commit()
    return PreparedQuestion(conv.id, conv.doc_set_id, ctx.user_id, turn_index, question, history)


# ---------------------------------------------------------------- chạy câu trả lời


def _sse(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


def _citation_payload(c: CitationOut) -> dict:
    return {
        "idx": c.idx,
        "citation_id": str(c.citation_id),
        "document_id": str(c.document_id),
        "filename": c.filename,
        "page": c.page,
    }


def _delta(span: Span) -> dict:
    return _sse("answer.delta", {"text": span.text, "citations": [_citation_payload(c) for c in span.citations]})


def _error_code(exc: BaseException) -> str:
    import anthropic

    if isinstance(exc, anthropic.APITimeoutError):  # lớp con của APIConnectionError — kiểm tra trước
        return "AI_TIMEOUT"
    if isinstance(exc, anthropic.APIConnectionError | anthropic.RateLimitError):
        return "AI_UNAVAILABLE"
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code >= 500:  # gồm 529 overloaded
        return "AI_UNAVAILABLE"
    return "INTERNAL"


_CANCELLED = object()


async def _next_or_cancel(agen: AsyncIterator, cancel: asyncio.Event):
    """Chờ sự kiện kế tiếp hoặc lệnh Dừng — dừng được trong ≤ 1 s kể cả khi Claude đang "nghĩ"."""
    nxt = asyncio.ensure_future(agen.__anext__())
    stopper = asyncio.ensure_future(cancel.wait())
    try:
        done, _ = await asyncio.wait({nxt, stopper}, return_when=asyncio.FIRST_COMPLETED)
    except BaseException:
        nxt.cancel()
        stopper.cancel()
        raise
    stopper.cancel()
    if nxt in done:
        return nxt.result()  # có thể ném StopAsyncIteration hoặc lỗi của SDK
    nxt.cancel()  # CancelledError trong generator → thoát `async with` → SDK đóng kết nối HTTP
    with contextlib.suppress(BaseException):
        await nxt
    return _CANCELLED


async def _save_turn(
    prep: PreparedQuestion,
    message_id: uuid.UUID,
    status: str,
    answer_type: str,
    answer: str,
    citations: tuple[CitationOut, ...],
) -> None:
    async with SessionLocal() as db:
        db.add(
            Turn(
                id=message_id,
                conversation_id=prep.conversation_id,
                turn_index=prep.turn_index,
                question=prep.question,
                answer=answer,
                answer_type=answer_type,
                status=status,
            )
        )
        await db.flush()
        db.add_all(
            Citation(
                id=c.citation_id,
                turn_id=message_id,
                idx=c.idx,
                document_id=c.document_id,
                chunk_id=c.chunk_id,
                filename=c.filename,
                page=c.page,
                snippet=c.snippet,
            )
            for c in citations
        )
        meta = {"answer_type": answer_type, "status": status, "citation_count": len(citations)}
        await record_audit(db, prep.user_id, "query", prep.doc_set_id, meta=meta)
        await db.commit()


async def _save_partial(
    prep: PreparedQuestion, message_id: uuid.UUID, filt: CitationFilter | None, status: str
) -> None:
    text, citations = filt.snapshot() if filt else ("", ())
    await _save_turn(prep, message_id, status, "answered" if citations else "not_found", text, citations)


async def run_answer(
    prep: PreparedQuestion,
    *,
    llm: LlmProtocol,
    embedder: EmbedderProtocol,
    registry: StreamRegistry,
    is_disconnected: Callable[[], Awaitable[bool]],
) -> AsyncIterator[dict]:
    """Async generator sự kiện SSE: answer.started → answer.delta* → completed | stopped | failed."""
    message_id = uuid.uuid4()
    cancel = registry.add(message_id, prep.user_id)
    filt: CitationFilter | None = None
    agen: AsyncIterator | None = None
    saved = False
    try:
        yield _sse("answer.started", {"message_id": str(message_id), "turn_index": prep.turn_index})

        # Câu đã viết lại chỉ dùng để tìm kiếm; Claude nhận câu gốc kèm lịch sử (US-011).
        query = prep.question
        if prep.turn_index > 0:
            query = await llm.rewrite_question(prep.history, prep.question)
        async with SessionLocal() as db:
            rows = await db.execute(
                select(Document.id, Document.filename)
                .where(
                    Document.doc_set_id == prep.doc_set_id,
                    Document.status.in_(("uploaded", "processing")),
                )
                .order_by(Document.uploaded_at.desc())
            )
            pending = [{"id": str(i), "filename": f} for i, f in rows.all()]  # AC-US001-3
            result = await retrieve(db, embedder, prep.doc_set_id, query)

        if result.not_found:  # không gọi Claude
            await _save_turn(prep, message_id, "completed", "not_found", "", ())
            saved = True
            yield _sse(
                "answer.completed",
                {
                    "message_id": str(message_id),
                    "answer_type": "not_found",
                    "citations": [],
                    "pending_documents": pending,
                },
            )
            return

        sources = [SourceRef(c.chunk_id, c.document_id, c.filename, c.page) for c in result.chunks]
        filt = CitationFilter(sources)
        agen = llm.stream_answer(prep.question, prep.history, result.chunks)
        while True:
            try:
                ev = await _next_or_cancel(agen, cancel)
            except StopAsyncIteration:
                ev = AnswerDone("", 0, 0)  # stream kết thúc mà không có AnswerDone

            if ev is _CANCELLED or cancel.is_set():
                await _save_partial(prep, message_id, filt, "stopped")
                saved = True
                yield _sse("answer.stopped", {"message_id": str(message_id)})
                return
            if await is_disconnected():
                await _save_partial(prep, message_id, filt, "incomplete")
                saved = True
                return

            if isinstance(ev, TextBlock):
                for span in filt.accept(ev):
                    yield _delta(span)
                continue

            if ev.stop_reason in ("end_turn", "stop_sequence"):
                out: FilterResult = filt.finalize()
                for span in out.late_spans:
                    yield _delta(span)
                await _save_turn(prep, message_id, "completed", out.answer_type, out.answer_text, out.citations)
                saved = True
                yield _sse(
                    "answer.completed",
                    {
                        "message_id": str(message_id),
                        "answer_type": out.answer_type,
                        "citations": [_citation_payload(c) for c in out.citations],
                        "pending_documents": pending,
                    },
                )
                return

            code = {"max_tokens": "MAX_TOKENS", "refusal": "AI_REFUSED"}.get(ev.stop_reason, "INTERNAL")
            log.info("message %s failed: stop_reason=%s", message_id, ev.stop_reason)
            await _save_partial(prep, message_id, filt, "incomplete")
            saved = True
            yield _sse("answer.failed", {"message_id": str(message_id), "code": code})
            return

    except (asyncio.CancelledError, GeneratorExit):
        # Người dùng đóng tab: sse-starlette hủy hoặc đóng generator. Lưu phần đã gửi rồi để hủy tiếp tục.
        if not saved:
            saved = True
            with contextlib.suppress(Exception):
                await asyncio.shield(_save_partial(prep, message_id, filt, "incomplete"))
        raise
    except Exception as exc:
        code = _error_code(exc)
        log.warning("message %s failed: %s (%s)", message_id, code, type(exc).__name__)
        if not saved:
            saved = True
            await _save_partial(prep, message_id, filt, "incomplete")
        yield _sse("answer.failed", {"message_id": str(message_id), "code": code})
    finally:
        registry.remove(message_id)
        if agen is not None:
            with contextlib.suppress(BaseException):
                await agen.aclose()


# ---------------------------------------------------------------- trích dẫn, đánh giá


async def get_citation(db: AsyncSession, ctx: AccessContext, citation_id: uuid.UUID) -> CitationDetailOut:
    row = (
        await db.execute(
            select(Citation, Conversation.doc_set_id)
            .join(Turn, Turn.id == Citation.turn_id)
            .join(Conversation, Conversation.id == Turn.conversation_id)
            .where(Citation.id == citation_id)
        )
    ).first()
    if row is None:
        raise not_found()
    cit, dsid = row
    ensure_member(ctx, dsid)  # admin hoặc người ngoài nhóm → 403 (AC-US013-2)
    if cit.removed or cit.filename is None:
        raise AppError("DOCUMENT_REMOVED", 410, "Tài liệu đã được gỡ khỏi bộ tài liệu")
    await record_audit(db, ctx.user_id, "view_citation", dsid, cit.document_id)
    await db.commit()
    return CitationDetailOut(
        document_id=cit.document_id, filename=cit.filename, page=cit.page, snippet=cit.snippet or ""
    )


async def submit_feedback(
    db: AsyncSession, ctx: AccessContext, turn_id: uuid.UUID, body: FeedbackIn
) -> FeedbackOut:
    row = (
        await db.execute(
            select(Turn.status, Conversation.user_id)
            .join(Conversation, Conversation.id == Turn.conversation_id)
            .where(Turn.id == turn_id)
        )
    ).first()
    if row is None:
        raise not_found()
    status, owner = row
    if owner != ctx.user_id:
        raise forbidden()
    if status != "completed":
        raise AppError("VALIDATION_ERROR", 422, "Chỉ đánh giá được câu trả lời đã hoàn tất")

    reason = body.reason if body.rating == "down" else None
    stmt = insert(Feedback).values(turn_id=turn_id, user_id=ctx.user_id, rating=body.rating, reason=reason)
    await db.execute(
        stmt.on_conflict_do_update(
            index_elements=[Feedback.turn_id, Feedback.user_id],
            set_={"rating": stmt.excluded.rating, "reason": stmt.excluded.reason},
        )
    )
    await db.commit()
    return FeedbackOut(turn_id=turn_id, rating=body.rating, reason=reason)
