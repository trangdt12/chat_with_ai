import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError

from app.models import EMBED_DIM, Chunk, Citation, Conversation, DocSet, Document, Turn, User


async def _doc_set_and_user(db):
    doc_set = DocSet(name="Bộ thử")
    user = User(email="u@test.local", display_name="U")
    db.add_all([doc_set, user])
    await db.flush()
    return doc_set, user


def _document(doc_set, user, filename="a.pdf") -> Document:
    return Document(
        doc_set_id=doc_set.id, filename=filename, size_bytes=10, file_path="/x", uploaded_by=user.id
    )


def _chunk(doc, content="nội dung") -> Chunk:
    return Chunk(
        document_id=doc.id,
        doc_set_id=doc.doc_set_id,
        page_number=1,
        chunk_index=0,
        content=content,
        embedding=[0.1] * EMBED_DIM,
    )


async def test_schema_has_tables_extensions_and_indexes(db):
    tables = set(
        await db.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
    ) - {"alembic_version"}
    assert tables == {
        "users", "doc_sets", "memberships", "sessions", "documents", "chunks",
        "conversations", "turns", "citations", "feedback", "audit_log",
    }
    extensions = set(await db.scalars(text("SELECT extname FROM pg_extension")))
    assert {"vector", "unaccent"} <= extensions
    indexes = set(await db.scalars(text("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")))
    assert {
        "chunks_embedding_hnsw", "chunks_tsv_gin", "chunks_doc_idx",
        "documents_list_idx", "turns_conv_idx", "audit_set_ts_idx",
    } <= indexes


async def test_unique_filename_per_doc_set(db):
    doc_set, user = await _doc_set_and_user(db)
    db.add(_document(doc_set, user))
    await db.flush()
    db.add(_document(doc_set, user))
    with pytest.raises(IntegrityError):
        await db.flush()


async def test_delete_document_cascades_chunks(db):
    doc_set, user = await _doc_set_and_user(db)
    doc = _document(doc_set, user)
    db.add(doc)
    await db.flush()
    chunk = _chunk(doc)
    conv = Conversation(user_id=user.id, doc_set_id=doc_set.id)
    db.add_all([chunk, conv])
    await db.flush()
    turn = Turn(conversation_id=conv.id, turn_index=0, question="q", answer_type="answered", status="completed")
    db.add(turn)
    await db.flush()
    db.add(Citation(turn_id=turn.id, idx=1, document_id=doc.id, chunk_id=chunk.id, filename="a.pdf", page=1))
    await db.commit()

    await db.execute(delete(Document).where(Document.id == doc.id))
    await db.commit()

    assert await db.scalar(select(func.count()).select_from(Chunk)) == 0
    assert await db.scalar(select(func.count()).select_from(Citation)) == 1


async def test_tsv_unaccent(db):
    doc_set, user = await _doc_set_and_user(db)
    doc = _document(doc_set, user)
    db.add(doc)
    await db.flush()
    db.add(_chunk(doc, "Thời hạn thanh toán"))
    await db.commit()

    found = await db.scalar(
        text("SELECT content FROM chunks WHERE tsv @@ websearch_to_tsquery('simple', f_unaccent(:q))"),
        {"q": "thoi han"},
    )
    assert found == "Thời hạn thanh toán"
