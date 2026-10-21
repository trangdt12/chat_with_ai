import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBED_DIM = 1024  # khớp BAAI/bge-m3

AUDIT_ACTIONS = (
    "login",
    "classification_confirm",
    "upload",
    "query",
    "view_citation",
    "view_file",
    "member_add",
    "member_remove",
    "role_change",
    "remove_document",
    "view_list",  # T-07: xem danh sách tài liệu, tối đa 1 lần/phút/người
)


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def _now() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class DocSet(Base):
    __tablename__ = "doc_sets"

    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (CheckConstraint(_in("role", ("member", "manager")), name="memberships_role_check"),)

    doc_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doc_sets.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    granted_at: Mapped[datetime] = _now()


class Session(Base):
    __tablename__ = "sessions"

    id_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = _now()
    last_seen_at: Mapped[datetime] = _now()
    classification_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("doc_set_id", "filename", name="documents_doc_set_filename_key"),
        CheckConstraint(_in("status", ("uploaded", "processing", "ready", "failed")), name="documents_status_check"),
        CheckConstraint("progress BETWEEN 0 AND 100", name="documents_progress_check"),
        Index("documents_list_idx", "doc_set_id", "uploaded_at"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    doc_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doc_sets.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    pages: Mapped[int | None] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="uploaded", server_default="uploaded")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    error_code: Mapped[str | None] = mapped_column(String(32))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = _now()


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    doc_set_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Cột sinh tự động trong DB — không bao giờ ghi khi insert.
    tsv: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('simple', f_unaccent(content))", persisted=True)
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM), nullable=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    doc_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doc_sets.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = _now()


class Turn(Base):
    __tablename__ = "turns"
    __table_args__ = (
        UniqueConstraint("conversation_id", "turn_index", name="turns_conversation_turn_key"),
        CheckConstraint(_in("answer_type", ("answered", "not_found", "clarification")), name="turns_answer_type_check"),
        CheckConstraint(_in("status", ("completed", "stopped", "incomplete")), name="turns_status_check"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False, default="")
    answer_type: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = _now()


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    turn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turns.id", ondelete="CASCADE"), nullable=False
    )
    idx: Mapped[int] = mapped_column(Integer, nullable=False)
    # Không FK tới documents/chunks: giữ được trích dẫn khi tài liệu bị gỡ (T-14).
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    filename: Mapped[str | None] = mapped_column(String(255))
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    snippet: Mapped[str | None] = mapped_column(String(300))
    removed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class Feedback(Base):
    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint(_in("rating", ("up", "down")), name="feedback_rating_check"),
    )

    turn_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("turns.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    rating: Mapped[str] = mapped_column(String(8), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(32))


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        CheckConstraint(_in("action", AUDIT_ACTIONS), name="audit_log_action_check"),
        Index("audit_set_ts_idx", "doc_set_id", "ts"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = _now()
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    doc_set_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    meta: Mapped[dict | None] = mapped_column(JSONB)
