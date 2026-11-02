import asyncio
import json
import time
import uuid

import anthropic
import httpx
import pytest
from pypdf import PdfReader
from sqlalchemy import delete, select, update

from app.config import get_settings
from app.ingestion.chunker import normalize_page
from app.ingestion.embeddings import FakeEmbedder
from app.ingestion.worker import process_document
from app.models import AuditLog, Citation, Document, Membership, Turn
from app.qa.llm import AnswerDone, RawCitation, TextBlock
from app.qa.streams import StreamRegistry
from tests.helpers import add_chunks, add_document
from tests.pdf_factory import make_pdf
from tests.sse_helpers import QUESTION, Env, parse_sse

CONTENT = "Thời hạn thanh toán là 30 ngày kể từ ngày nhận hóa đơn. Chậm giao hàng được gia hạn 15 ngày."


@pytest.fixture
async def env(app, db, seeded, login_as, monkeypatch):
    # FakeEmbedder (túi từ): câu liên quan có cosine ≈ 0,28–0,40, câu không liên quan ≈ 0,11–0,19.
    # Hạ τ để các test luồng LLM không phụ thuộc vào biên sát 0,35.
    monkeypatch.setattr(get_settings(), "retrieval_not_found_tau", 0.25)
    doc = await add_document(db, seeded.doc_set_id, seeded.users["lan@demo.local"], "HopDongKhung.pdf")
    await add_chunks(db, doc, [CONTENT], page=14)
    e = Env(app, db, seeded, await login_as("lan@demo.local"))
    e.doc = doc
    yield e
    app.dependency_overrides.clear()


async def _turn(db, message_id) -> Turn:
    db.expire_all()
    return await db.get(Turn, message_id)


async def test_ask_happy_path_event_order(env):
    cid = await env.conversation()
    events = await env.ask_events(cid)
    names = [n for n, _ in events]
    assert names[0] == "answer.started" and names[-1] == "answer.completed"
    assert names.count("answer.delta") >= 1 and set(names[1:-1]) == {"answer.delta"}

    started, completed = events[0][1], events[-1][1]
    assert started["turn_index"] == 0
    assert completed["answer_type"] == "answered"
    cit = completed["citations"][0]
    assert (cit["idx"], cit["filename"], cit["page"], cit["document_id"]) == (
        1, "HopDongKhung.pdf", 14, str(env.doc.id),
    )
    delta_ids = {c["citation_id"] for n, d in events if n == "answer.delta" for c in d["citations"]}
    assert delta_ids == {c["citation_id"] for c in completed["citations"]}

    turn = await _turn(env.db, started["message_id"])
    assert (turn.status, turn.answer_type, turn.turn_index) == ("completed", "answered", 0)
    assert turn.answer == "".join(d["text"] for n, d in events if n == "answer.delta")
    stored = (await env.db.scalars(select(Citation).where(Citation.turn_id == turn.id))).all()
    assert {str(c.id) for c in stored} == delta_ids
    assert all(len(c.snippet) <= 300 for c in stored)
    assert env.embedder.queries == [QUESTION]  # lượt đầu không viết lại câu hỏi
    assert env.llm.rewrite_calls == []


async def test_ask_not_found_skips_llm(env):
    cid = await env.conversation()
    events = await env.ask_events(cid, "Thủ đô của Pháp là gì?")
    assert [n for n, _ in events] == ["answer.started", "answer.completed"]
    assert events[-1][1]["answer_type"] == "not_found"
    assert env.llm.answer_calls == []
    turn = await _turn(env.db, events[0][1]["message_id"])
    assert (turn.status, turn.answer_type, turn.answer) == ("completed", "not_found", "")


async def test_ask_llm_not_found_marker(env):
    cid = await env.conversation()
    events = await env.ask_events(cid, "Thời hạn thanh toán không có trong tài liệu?")
    assert len(env.llm.answer_calls) == 1  # đi qua Claude (giả) → marker [KHONG_TIM_THAY]
    assert events[-1][1]["answer_type"] == "not_found"
    assert "answer.delta" not in [n for n, _ in events]


async def test_ask_pending_documents(env):
    proc = await add_document(
        env.db, env.seeded.doc_set_id, env.seeded.users["lan@demo.local"], "BaoGia_v3.pdf", status="processing"
    )
    cid = await env.conversation()
    events = await env.ask_events(cid)
    assert events[-1][1]["pending_documents"] == [{"id": str(proc.id), "filename": "BaoGia_v3.pdf"}]


async def test_ask_followup_uses_rewrite(env):
    cid = await env.conversation()
    await env.ask_events(cid)
    events = await env.ask_events(cid, "Điều khoản đó có ngoại lệ không?")
    assert events[0][1]["turn_index"] == 1
    assert len(env.llm.answer_calls) == 2
    [(history, question)] = env.llm.rewrite_calls
    assert question == "Điều khoản đó có ngoại lệ không?"
    assert [q for q, _ in history] == [QUESTION]
    assert env.embedder.queries[-1] == f"{QUESTION} Điều khoản đó có ngoại lệ không?"
    # Claude nhận câu gốc kèm lịch sử
    assert env.llm.answer_calls[-1]["question"] == "Điều khoản đó có ngoại lệ không?"
    assert [q for q, _ in env.llm.answer_calls[-1]["history"]] == [QUESTION]


async def test_new_conversation_no_history(env):
    await env.ask_events(await env.conversation())
    events = await env.ask_events(await env.conversation(), "Thời hạn thanh toán đó có ngoại lệ gì?")
    assert events[0][1]["turn_index"] == 0
    assert len(env.llm.answer_calls) == 2
    assert env.llm.answer_calls[-1]["history"] == []
    assert len(env.llm.rewrite_calls) == 0


async def test_ask_validation_and_permissions(env, login_as):
    cid = await env.conversation()
    for bad in ("", "   ", "x" * 2001):
        r = await env.ask(cid, bad)
        assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR"

    tuan = await login_as("tuan@demo.local")
    r = await tuan.post(f"/api/v1/doc-sets/{env.seeded.doc_set_id}/conversations")
    assert r.status_code == 403
    assert (await env.ask(cid, client=tuan)).status_code == 404  # hội thoại không thuộc người gọi

    await env.db.execute(update(Document).values(status="processing"))
    await env.db.commit()
    r = await env.ask(cid)
    assert r.status_code == 409 and r.json()["code"] == "NO_READY_DOCUMENTS"

    await env.db.execute(delete(Membership).where(Membership.user_id == env.seeded.users["lan@demo.local"]))
    await env.db.commit()
    r = await env.ask(cid)
    assert r.status_code == 403
    assert "HopDongKhung" not in r.text


async def _wait_active(registry: StreamRegistry, timeout: float = 5):
    deadline = time.monotonic() + timeout
    while not registry._streams:
        assert time.monotonic() < deadline, "stream chưa bắt đầu"
        await asyncio.sleep(0.01)
    return next(iter(registry._streams))


def _slow_script(n: int = 50) -> list:
    return [TextBlock(f"Khối {i}. ", (RawCitation(0, "Thời hạn thanh toán là 30 ngày"),)) for i in range(n)] + [
        AnswerDone("end_turn", 1, 1)
    ]


async def test_stop_mid_stream(env):
    env.llm.script, env.llm.delay = _slow_script(), 0.5
    cid = await env.conversation()
    task = asyncio.create_task(env.ask(cid))
    mid = await _wait_active(env.registry)
    await asyncio.sleep(0.6)  # để ít nhất 1 khối đã gửi
    started = time.monotonic()
    assert (await env.lan.post(f"/api/v1/messages/{mid}/stop")).status_code == 202
    r = await asyncio.wait_for(task, 5)
    assert time.monotonic() - started <= 1.0
    events = parse_sse(r.text)
    assert events[-1] == ("answer.stopped", {"message_id": str(mid)})
    turn = await _turn(env.db, mid)
    assert turn.status == "stopped"
    assert turn.answer == "".join(d["text"] for n, d in events if n == "answer.delta")


async def test_stop_while_llm_thinking(env):
    env.llm.script, env.llm.delay = [TextBlock("A", (RawCitation(0, "x"),)), AnswerDone("end_turn", 1, 1)], 30
    cid = await env.conversation()
    task = asyncio.create_task(env.ask(cid))
    mid = await _wait_active(env.registry)
    await asyncio.sleep(0.2)
    started = time.monotonic()
    await env.lan.post(f"/api/v1/messages/{mid}/stop")
    r = await asyncio.wait_for(task, 5)
    assert time.monotonic() - started <= 1.0
    assert parse_sse(r.text)[-1][0] == "answer.stopped"


async def test_stop_other_user_ignored(env, login_as):
    env.llm.script, env.llm.delay = _slow_script(5), 0.1
    minh = await login_as("minh@demo.local")
    cid = await env.conversation()
    task = asyncio.create_task(env.ask(cid))
    mid = await _wait_active(env.registry)
    assert (await minh.post(f"/api/v1/messages/{mid}/stop")).status_code == 202
    events = parse_sse((await asyncio.wait_for(task, 5)).text)
    assert events[-1][0] == "answer.completed"


async def test_llm_error_mid_stream(env):
    err = anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"))
    env.llm.script = [TextBlock("Thời hạn là 30 ngày", (RawCitation(0, "30 ngày"),)), err]
    cid = await env.conversation()
    events = await env.ask_events(cid)
    assert events[-1][0] == "answer.failed"
    assert events[-1][1]["code"] == "AI_UNAVAILABLE"
    turn = await _turn(env.db, events[0][1]["message_id"])
    assert (turn.status, turn.answer_type, turn.answer) == ("incomplete", "answered", "Thời hạn là 30 ngày")


async def test_max_tokens_is_failed(env):
    env.llm.script = [TextBlock("Thời hạn là 30 ngày", (RawCitation(0, "30 ngày"),)), AnswerDone("max_tokens", 1, 1)]
    events = await env.ask_events(await env.conversation())
    assert events[-1] == ("answer.failed", {"message_id": events[0][1]["message_id"], "code": "MAX_TOKENS"})
    assert (await _turn(env.db, events[0][1]["message_id"])).status == "incomplete"


async def test_get_citation_ok_removed_forbidden(env, login_as):
    events = await env.ask_events(await env.conversation())
    citation_id = events[-1][1]["citations"][0]["citation_id"]

    r = await env.lan.get(f"/api/v1/citations/{citation_id}")
    assert r.status_code == 200
    body = r.json()
    assert (body["filename"], body["page"], body["document_id"]) == ("HopDongKhung.pdf", 14, str(env.doc.id))
    assert 0 < len(body["snippet"]) <= 300
    assert await env.db.scalar(select(AuditLog.id).where(AuditLog.action == "view_citation"))

    for email in ("hung@demo.local", "tuan@demo.local"):
        c = await login_as(email)
        assert (await c.get(f"/api/v1/citations/{citation_id}")).status_code == 403

    await env.db.execute(update(Citation).values(removed=True, snippet=None, filename=None, chunk_id=None))
    await env.db.commit()
    r = await env.lan.get(f"/api/v1/citations/{citation_id}")
    assert r.status_code == 410 and r.json()["code"] == "DOCUMENT_REMOVED"


async def test_no_content_in_audit_meta(env):
    cid = await env.conversation()
    await env.ask_events(cid)
    await env.ask_events(cid, "Thủ đô của Pháp là gì?")
    metas = (await env.db.scalars(select(AuditLog.meta).where(AuditLog.action == "query"))).all()
    assert len(metas) == 2
    for meta in metas:
        assert set(meta) == {"answer_type", "status", "citation_count"}
        dumped = json.dumps(meta, ensure_ascii=False)
        assert "Thời hạn" not in dumped and "Pháp" not in dumped


# ------------------------------------------------- đường xương sống US-001 + US-009 (docs/test/test-cases.yaml)

PAGES3 = [
    "Hop dong khung so HD-2024-017 ky giua Cong ty A va Cong ty B.",
    "Thoi han thanh toan la 30 ngay ke tu ngay nhan hoa don hop le.",
    "Phan mem duoc bao hanh 12 thang ke tu ngay nghiem thu.",
]
QUESTIONS3 = [
    "Hợp đồng khung số hiệu là gì?",
    "Thời hạn thanh toán là bao lâu?",
    "Phần mềm được bảo hành bao lâu?",
]


@pytest.fixture
async def bare_env(app, db, seeded, login_as, monkeypatch):
    """Như `env` nhưng bộ tài liệu trống: tài liệu được đưa qua worker thật để pages/page_number là dữ liệu thật."""
    monkeypatch.setattr(get_settings(), "retrieval_not_found_tau", 0.25)
    e = Env(app, db, seeded, await login_as("lan@demo.local"))
    yield e
    app.dependency_overrides.clear()


async def _ingest(e: Env, filename: str, pages: list[str]) -> Document:
    doc = await add_document(
        e.db, e.seeded.doc_set_id, e.seeded.users["lan@demo.local"], filename, status="uploaded", data=make_pdf(pages)
    )
    doc_id = doc.id
    await process_document(doc_id, FakeEmbedder())
    e.db.expire_all()
    doc = await e.db.get(Document, doc_id)
    assert (doc.status, doc.pages) == ("ready", len(pages))
    return doc


def _norm(s: str) -> str:
    return " ".join(normalize_page(s).split()).lower()


async def test_answer_cites_only_source_file(bare_env):
    """TC-008 · AC-US001-2: bộ có 2 file, hỏi thông tin chỉ có ở BaoGia_v3.pdf → có trích dẫn tới file đó."""
    await _ingest(bare_env, "HopDongKhung.pdf", PAGES3)
    await _ingest(
        bare_env,
        "BaoGia_v3.pdf",
        ["Bao gia v3. Goi phan mem ban quyen gia 450.000.000 dong. Trien khai va dao tao 120 trieu dong."],
    )
    events = await bare_env.ask_events(
        await bare_env.conversation(), "Giá gói phần mềm bản quyền trong báo giá là bao nhiêu?"
    )
    done = events[-1][1]
    assert done["answer_type"] == "answered"
    assert len(done["citations"]) >= 1
    assert any(c["filename"] == "BaoGia_v3.pdf" for c in done["citations"]), done["citations"]


async def test_pending_documents_exact_set(bare_env):
    """TC-012 · AC-US001-3: pending = đúng uploaded ∪ processing; không có failed; không trích dẫn file pending."""
    e = bare_env
    await _ingest(e, "A.pdf", PAGES3)
    lan_id = e.seeded.users["lan@demo.local"]
    others = {}
    for name, status in (("B.pdf", "uploaded"), ("C.pdf", "processing"), ("D.pdf", "failed")):
        doc = await add_document(e.db, e.seeded.doc_set_id, lan_id, name, status=status)
        await add_chunks(e.db, doc, [PAGES3[1]], page=1)  # bẫy: cùng nội dung với A nhưng chưa sẵn sàng
        others[name] = doc.id

    done = (await e.ask_events(await e.conversation(), QUESTIONS3[1]))[-1][1]
    assert done["answer_type"] == "answered"
    assert {d["filename"] for d in done["pending_documents"]} == {"B.pdf", "C.pdf"}
    assert not {c["document_id"] for c in done["citations"]} & {str(i) for i in others.values()}

    done = (await e.ask_events(await e.conversation(), "Thủ đô của Pháp là gì?"))[-1][1]
    assert done["answer_type"] == "not_found"
    assert {d["filename"] for d in done["pending_documents"]} == {"B.pdf", "C.pdf"}


async def _ask_each(e: Env) -> list[dict]:
    return [(await e.ask_events(await e.conversation(), q))[-1][1] for q in QUESTIONS3]


async def test_answered_citation_invariants(bare_env):
    """TC-020 · AC-US009-1: answered ⇒ ≥ 1 trích dẫn, filename khác rỗng, 1 ≤ page ≤ documents.pages."""
    await _ingest(bare_env, "HopDongKhung.pdf", PAGES3)
    for done in await _ask_each(bare_env):
        assert done["answer_type"] == "answered"
        assert len(done["citations"]) >= 1
        for c in done["citations"]:
            doc = await bare_env.db.get(Document, uuid.UUID(c["document_id"]))
            assert c["filename"] != "" and isinstance(c["page"], int)
            assert 1 <= c["page"] <= doc.pages


async def test_snippet_is_on_cited_page(bare_env):
    """TC-029 · AC-US009-3a: đoạn trích (đã chuẩn hóa) là chuỗi con của chữ trên trang được nêu."""
    doc = await _ingest(bare_env, "HopDongKhung.pdf", PAGES3)
    reader = PdfReader(doc.file_path)
    checked = 0
    for done in await _ask_each(bare_env):
        for c in done["citations"]:
            cit = await bare_env.db.get(Citation, uuid.UUID(c["citation_id"]))
            page_text = reader.pages[cit.page - 1].extract_text()
            assert _norm(cit.snippet) in _norm(page_text), (cit.page, cit.snippet)
            checked += 1
    assert checked >= len(QUESTIONS3)


async def test_uncited_blocks_never_streamed_or_saved(env):
    """TC-034 · AC-US009-4: khối không có nguồn (đầu và cuối) không tới người dùng và không được lưu."""
    env.llm.script = [
        TextBlock("Theo kinh nghiệm thường là 99 ngày.", ()),
        TextBlock("Thời hạn là 30 ngày.", (RawCitation(0, "30 ngày"),)),
        TextBlock("Có thể kéo dài tới 7 ngày nữa theo Luật Thương mại.", ()),
        AnswerDone("end_turn", 1, 1),
    ]
    events = await env.ask_events(await env.conversation())
    streamed = "".join(d["text"] for n, d in events if n == "answer.delta")
    assert "99 ngày" not in streamed and "7 ngày" not in streamed and "30 ngày" in streamed
    assert events[-1][1]["answer_type"] == "answered"
    assert (await _turn(env.db, events[0][1]["message_id"])).answer == streamed


async def test_all_uncited_becomes_not_found(env):
    """TC-035 · AC-US009-4: không khối nào có nguồn → not_found, không delta, câu trả lời rỗng."""
    env.llm.script = [TextBlock("Thời hạn là 30 ngày.", ()), AnswerDone("end_turn", 1, 1)]
    events = await env.ask_events(await env.conversation())
    assert [n for n, _ in events] == ["answer.started", "answer.completed"]
    assert events[-1][1]["answer_type"] == "not_found" and events[-1][1]["citations"] == []
    turn = await _turn(env.db, events[0][1]["message_id"])
    assert (turn.answer, turn.answer_type) == ("", "not_found")
