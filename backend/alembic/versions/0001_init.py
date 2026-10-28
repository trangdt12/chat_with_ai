"""init: extension, 11 bảng, chỉ mục vector và full-text

Revision ID: 0001
Revises:
Create Date: 2026-10-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBED_DIM = 1024  # khớp BAAI/bge-m3; đổi model thì phải đổi số chiều và tạo lại chỉ mục

# Ghi cứng tại đây (không import từ app.models) để migration không đổi theo code.
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
    "view_list",
)


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


def _uuid_pk() -> sa.Column:
    return sa.Column("id", UUID(as_uuid=True), primary_key=True)


def _ts(name: str, nullable: bool = False) -> sa.Column:
    if nullable:
        return sa.Column(name, sa.DateTime(timezone=True), nullable=True)
    return sa.Column(name, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def _fk(name: str, target: str, nullable: bool = False, ondelete: str | None = "CASCADE") -> sa.Column:
    return sa.Column(name, UUID(as_uuid=True), sa.ForeignKey(target, ondelete=ondelete), nullable=nullable)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    # unaccent() không IMMUTABLE nên bọc lại để dùng trong cột sinh tự động.
    op.execute(
        "CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text "
        "LANGUAGE sql IMMUTABLE PARALLEL SAFE "
        "AS $$ SELECT public.unaccent('public.unaccent', $1) $$"
    )

    op.create_table(
        "users",
        _uuid_pk(),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "doc_sets",
        _uuid_pk(),
        sa.Column("name", sa.String(200), nullable=False),
    )

    op.create_table(
        "memberships",
        sa.Column(
            "doc_set_id", UUID(as_uuid=True), sa.ForeignKey("doc_sets.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String(16), nullable=False),
        _ts("granted_at"),
        sa.CheckConstraint(_in("role", ("member", "manager")), name="memberships_role_check"),
    )

    op.create_table(
        "sessions",
        sa.Column("id_hash", sa.String(64), primary_key=True),
        _fk("user_id", "users.id"),
        _ts("created_at"),
        _ts("last_seen_at"),
        _ts("classification_confirmed_at", nullable=True),
    )

    op.create_table(
        "documents",
        _uuid_pk(),
        _fk("doc_set_id", "doc_sets.id"),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("pages", sa.Integer),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="uploaded"),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(32)),
        sa.Column("file_path", sa.Text, nullable=False),
        _fk("uploaded_by", "users.id", ondelete=None),
        _ts("uploaded_at"),
        sa.UniqueConstraint("doc_set_id", "filename", name="documents_doc_set_filename_key"),
        sa.CheckConstraint(
            _in("status", ("uploaded", "processing", "ready", "failed")), name="documents_status_check"
        ),
        sa.CheckConstraint("progress BETWEEN 0 AND 100", name="documents_progress_check"),
    )
    op.execute("CREATE INDEX documents_list_idx ON documents (doc_set_id, uploaded_at DESC)")

    op.create_table(
        "chunks",
        _uuid_pk(),
        _fk("document_id", "documents.id"),
        sa.Column("doc_set_id", UUID(as_uuid=True), nullable=False),
        sa.Column("page_number", sa.Integer, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column(
            "tsv",
            TSVECTOR,
            sa.Computed("to_tsvector('simple', f_unaccent(content))", persisted=True),
        ),
        sa.Column("embedding", Vector(EMBED_DIM), nullable=False),
    )
    op.execute(
        "CREATE INDEX chunks_embedding_hnsw ON chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )
    op.execute("CREATE INDEX chunks_tsv_gin ON chunks USING gin (tsv)")
    op.execute("CREATE INDEX chunks_doc_idx ON chunks (doc_set_id, document_id)")

    op.create_table(
        "conversations",
        _uuid_pk(),
        _fk("user_id", "users.id"),
        _fk("doc_set_id", "doc_sets.id"),
        _ts("created_at"),
    )

    op.create_table(
        "turns",
        _uuid_pk(),
        _fk("conversation_id", "conversations.id"),
        sa.Column("turn_index", sa.Integer, nullable=False),
        sa.Column("question", sa.Text, nullable=False),
        sa.Column("answer", sa.Text, nullable=False, server_default=""),
        sa.Column("answer_type", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        _ts("created_at"),
        sa.UniqueConstraint("conversation_id", "turn_index", name="turns_conversation_turn_key"),
        sa.CheckConstraint(
            _in("answer_type", ("answered", "not_found", "clarification")), name="turns_answer_type_check"
        ),
        sa.CheckConstraint(_in("status", ("completed", "stopped", "incomplete")), name="turns_status_check"),
    )
    op.execute("CREATE INDEX turns_conv_idx ON turns (conversation_id, turn_index)")

    op.create_table(
        "citations",
        _uuid_pk(),
        _fk("turn_id", "turns.id"),
        sa.Column("idx", sa.Integer, nullable=False),
        # Không FK tới documents/chunks: giữ được trích dẫn khi tài liệu bị gỡ (T-14).
        sa.Column("document_id", UUID(as_uuid=True)),
        sa.Column("chunk_id", UUID(as_uuid=True)),
        sa.Column("filename", sa.String(255)),
        sa.Column("page", sa.Integer, nullable=False),
        sa.Column("snippet", sa.String(300)),
        sa.Column("removed", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "feedback",
        sa.Column("turn_id", UUID(as_uuid=True), sa.ForeignKey("turns.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("rating", sa.String(8), nullable=False),
        sa.Column("reason", sa.String(32)),
        sa.CheckConstraint(_in("rating", ("up", "down")), name="feedback_rating_check"),
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        _ts("ts"),
        sa.Column("user_id", UUID(as_uuid=True)),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("doc_set_id", UUID(as_uuid=True)),
        sa.Column("document_id", UUID(as_uuid=True)),
        sa.Column("meta", JSONB),
        sa.CheckConstraint(_in("action", AUDIT_ACTIONS), name="audit_log_action_check"),
    )
    op.execute("CREATE INDEX audit_set_ts_idx ON audit_log (doc_set_id, ts)")


def downgrade() -> None:
    for table in (
        "audit_log",
        "feedback",
        "citations",
        "turns",
        "conversations",
        "chunks",
        "documents",
        "sessions",
        "memberships",
        "doc_sets",
        "users",
    ):
        op.drop_table(table)
    op.execute("DROP FUNCTION IF EXISTS f_unaccent(text)")
    op.execute("DROP EXTENSION IF EXISTS unaccent")
    op.execute("DROP EXTENSION IF EXISTS vector")
