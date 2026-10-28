import uuid

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.auth.deps import current_ctx, require_member
from app.auth.policy import AccessContext
from app.db import get_db
from app.ingestion.embeddings import EmbedderProtocol, get_embedder
from app.qa import service
from app.qa.llm import LlmProtocol, get_llm
from app.qa.schemas import CitationDetailOut, ConversationOut, FeedbackIn, FeedbackOut, QuestionIn
from app.qa.streams import StreamRegistry, registry

router = APIRouter()

KEEP_ALIVE_SECONDS = 15


# Dependency riêng để test thay bằng FakeLlmClient / FakeEmbedder qua app.dependency_overrides.
def llm_dep() -> LlmProtocol:
    return get_llm()


def embedder_dep() -> EmbedderProtocol:
    return get_embedder()


def registry_dep() -> StreamRegistry:
    return registry


@router.post("/doc-sets/{dsid}/conversations", status_code=201)
async def create_conversation(
    dsid: uuid.UUID, ctx: AccessContext = Depends(require_member), db: AsyncSession = Depends(get_db)
) -> ConversationOut:
    return ConversationOut(conversation_id=await service.create_conversation(db, ctx, dsid))


@router.post("/conversations/{cid}/messages")
async def ask(
    cid: uuid.UUID,
    body: QuestionIn,
    request: Request,
    ctx: AccessContext = Depends(current_ctx),
    db: AsyncSession = Depends(get_db),
    llm: LlmProtocol = Depends(llm_dep),
    embedder: EmbedderProtocol = Depends(embedder_dep),
    streams: StreamRegistry = Depends(registry_dep),
) -> EventSourceResponse:
    # Kiểm tra xong mới mở stream: lỗi ở bước này trả JSON thường.
    prep = await service.prepare_question(db, ctx, cid, body.question)
    events = service.run_answer(
        prep, llm=llm, embedder=embedder, registry=streams, is_disconnected=request.is_disconnected
    )
    return EventSourceResponse(events, ping=KEEP_ALIVE_SECONDS, headers={"Cache-Control": "no-store"})


@router.post("/messages/{mid}/stop", status_code=202)
async def stop(
    mid: uuid.UUID, ctx: AccessContext = Depends(current_ctx), streams: StreamRegistry = Depends(registry_dep)
) -> Response:
    streams.stop(mid, ctx.user_id)
    return Response(status_code=202)


@router.get("/citations/{citation_id}")
async def get_citation(
    citation_id: uuid.UUID, ctx: AccessContext = Depends(current_ctx), db: AsyncSession = Depends(get_db)
) -> CitationDetailOut:
    return await service.get_citation(db, ctx, citation_id)


@router.put("/messages/{mid}/feedback")
async def submit_feedback(
    mid: uuid.UUID,
    body: FeedbackIn,
    ctx: AccessContext = Depends(current_ctx),
    db: AsyncSession = Depends(get_db),
) -> FeedbackOut:
    return await service.submit_feedback(db, ctx, mid, body)
