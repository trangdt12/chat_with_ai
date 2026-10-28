"""Hàm dựng dữ liệu dùng chung cho test."""

import uuid
from datetime import UTC, datetime, timedelta

from app.documents import storage
from app.ingestion.embeddings import FakeEmbedder, embedding_text
from app.models import Chunk, Document
from tests.pdf_factory import sample_pdf


async def add_document(db, doc_set_id, user_id, filename="a.pdf", *, status="ready", minutes_ago=0, data=None):
    """Tạo tài liệu trực tiếp trong DB + file trên đĩa (dùng chung cho các test khác)."""
    doc_id = uuid.uuid4()
    path = storage.file_path_for(doc_set_id, doc_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = data if data is not None else sample_pdf()
    path.write_bytes(content)
    doc = Document(
        id=doc_id,
        doc_set_id=doc_set_id,
        filename=filename,
        pages=2,
        size_bytes=len(content),
        status=status,
        progress=100 if status == "ready" else 0,
        file_path=str(path),
        uploaded_by=user_id,
        uploaded_at=datetime.now(UTC) - timedelta(minutes=minutes_ago),
    )
    db.add(doc)
    await db.commit()
    return doc


async def add_chunks(db, doc, contents: list[str], page: int = 1) -> list[Chunk]:
    """Thêm đoạn văn cho tài liệu, embedding bằng FakeEmbedder (như worker làm)."""
    embedder = FakeEmbedder()
    chunks = [
        Chunk(
            document_id=doc.id,
            doc_set_id=doc.doc_set_id,
            page_number=page,
            chunk_index=i,
            content=content,
            embedding=embedder.embed_documents([embedding_text(doc.filename, page, content)])[0],
        )
        for i, content in enumerate(contents)
    ]
    db.add_all(chunks)
    await db.commit()
    return chunks
