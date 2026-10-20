-- =============================================================================
-- Chat với tài liệu (MVP) — Information View (IEEE 1016-2009)
-- Tài liệu: Blueprint SDD-CWD-001 v0.1 · Nguồn: SAD-CWD-001 v0.2 §3.1
-- CSDL: PostgreSQL 16 + pgvector (>= 0.8) + unaccent
-- Quy ước: UUIDv7 sinh ở tầng ứng dụng; mọi thời gian là timestamptz (UTC).
-- Mọi giới hạn [GĐ] (50 file, 200 trang, 20 MB, 2.000 ký tự, 300 ký tự) lấy từ PRD v0.4.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE SCHEMA IF NOT EXISTS access;
CREATE SCHEMA IF NOT EXISTS documents;
CREATE SCHEMA IF NOT EXISTS qa;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS billing;

-- unaccent() mặc định là STABLE; cần một wrapper IMMUTABLE để dùng trong generated column.
CREATE OR REPLACE FUNCTION documents.f_unaccent(text)
RETURNS text LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;

-- -----------------------------------------------------------------------------
-- documents: bộ tài liệu (DE-DOC)
-- -----------------------------------------------------------------------------
CREATE TABLE documents.doc_sets (
    id             uuid PRIMARY KEY,
    name           text        NOT NULL UNIQUE,
    max_documents  integer     NOT NULL DEFAULT 50 CHECK (max_documents > 0),   -- BR-002
    created_at     timestamptz NOT NULL DEFAULT now()
);

-- -----------------------------------------------------------------------------
-- access: người dùng, nhóm truy cập, phiên, xác nhận phân loại (DE-ACC)
-- -----------------------------------------------------------------------------
CREATE TABLE access.users (
    id             uuid PRIMARY KEY,
    entra_oid      text        NOT NULL UNIQUE,          -- object id trong Entra ID
    email          text        NOT NULL,
    display_name   text        NOT NULL,
    is_admin       boolean     NOT NULL DEFAULT false,   -- Quản trị viên CNTT (BRU-007)
    created_at     timestamptz NOT NULL DEFAULT now(),
    last_login_at  timestamptz
);
CREATE UNIQUE INDEX users_email_lower_uq ON access.users (lower(email));

CREATE TABLE access.memberships (
    doc_set_id  uuid        NOT NULL REFERENCES documents.doc_sets(id) ON DELETE CASCADE,
    user_id     uuid        NOT NULL REFERENCES access.users(id)        ON DELETE CASCADE,
    role        text        NOT NULL CHECK (role IN ('member', 'manager')),  -- manager = Quản lý bộ tài liệu (OI-03)
    granted_by  uuid        REFERENCES access.users(id),
    granted_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (doc_set_id, user_id)
);
CREATE INDEX memberships_user_idx ON access.memberships (user_id);

CREATE TABLE access.sessions (
    id_hash          bytea       PRIMARY KEY,            -- SHA-256 của session id; không lưu bản rõ
    user_id          uuid        NOT NULL REFERENCES access.users(id) ON DELETE CASCADE,
    created_at       timestamptz NOT NULL DEFAULT now(),
    last_seen_at     timestamptz NOT NULL DEFAULT now(),
    expires_idle_at  timestamptz NOT NULL,               -- last_seen_at + 8 giờ (NFR-009)
    csrf_secret      bytea       NOT NULL,
    user_agent_hash  bytea,
    revoked_at       timestamptz
);
CREATE INDEX sessions_user_idx    ON access.sessions (user_id);
CREATE INDEX sessions_expires_idx ON access.sessions (expires_idle_at);

CREATE TABLE access.classification_confirmations (    -- UC-03, BRU-001
    id                 uuid        PRIMARY KEY,
    user_id            uuid        NOT NULL REFERENCES access.users(id) ON DELETE CASCADE,
    session_id_hash    bytea       NOT NULL REFERENCES access.sessions(id_hash) ON DELETE CASCADE,
    doc_set_id         uuid        NOT NULL REFERENCES documents.doc_sets(id) ON DELETE CASCADE,
    statement_version  integer     NOT NULL,
    confirmed_at       timestamptz NOT NULL DEFAULT now(),
    UNIQUE (session_id_hash, doc_set_id)
);

-- -----------------------------------------------------------------------------
-- documents: tài liệu và đoạn văn (DE-DOC, DE-ING)
-- -----------------------------------------------------------------------------
CREATE TABLE documents.documents (
    id           uuid        PRIMARY KEY,
    doc_set_id   uuid        NOT NULL REFERENCES documents.doc_sets(id) ON DELETE CASCADE,
    filename     text        NOT NULL CHECK (char_length(filename) BETWEEN 1 AND 255),
    pages        integer     CHECK (pages BETWEEN 1 AND 200),                    -- NULL cho tới khi xử lý
    size_bytes   bigint      NOT NULL CHECK (size_bytes BETWEEN 1 AND 20971520), -- ≤ 20 MB
    status       text        NOT NULL DEFAULT 'uploaded'
                 CHECK (status IN ('uploaded','processing','ready','failed','purging','purge_pending')),
    progress     smallint    NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    error_code   text        CHECK (error_code IN ('corrupt','encrypted','no_text','too_many_pages','timeout')),
    s3_key       text        NOT NULL UNIQUE,
    sha256       char(64)    NOT NULL,
    uploaded_by  uuid        NOT NULL REFERENCES access.users(id),
    uploaded_at  timestamptz NOT NULL DEFAULT now(),
    ready_at     timestamptz,
    UNIQUE (doc_set_id, filename),                                             -- trùng tên → đổi "ten (2).pdf" (E-09)
    -- failed bắt buộc có error_code; error_code chỉ được tồn tại khi failed hoặc khi đang gỡ một tài liệu đã failed
    CHECK (status <> 'failed' OR error_code IS NOT NULL),
    CHECK (error_code IS NULL OR status IN ('failed','purging','purge_pending'))
);
CREATE INDEX documents_set_uploaded_idx ON documents.documents (doc_set_id, uploaded_at DESC);
CREATE INDEX documents_pending_idx      ON documents.documents (doc_set_id)
    WHERE status IN ('uploaded', 'processing');                               -- AC-US001-3

CREATE TABLE documents.chunks (
    id           uuid         PRIMARY KEY,
    document_id  uuid         NOT NULL REFERENCES documents.documents(id) ON DELETE CASCADE,  -- BR-017
    doc_set_id   uuid         NOT NULL,                                       -- phi chuẩn hóa để lọc + RLS
    page_number  integer      NOT NULL CHECK (page_number >= 1),
    chunk_index  integer      NOT NULL CHECK (chunk_index >= 0),
    content      text         NOT NULL CHECK (char_length(content) <= 1800),  -- DD-02
    block_ends   integer[]    NOT NULL,                                       -- vị trí kết thúc các khối ≤ 300 ký tự (DD-03)
    token_count  integer      NOT NULL,
    tsv          tsvector     GENERATED ALWAYS AS
                 (to_tsvector('simple'::regconfig, documents.f_unaccent(content))) STORED,
    embedding    vector(1024) NOT NULL,                                       -- Cohere Embed Multilingual
    UNIQUE (document_id, chunk_index)
);
CREATE INDEX chunks_embedding_hnsw ON documents.chunks
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX chunks_tsv_gin   ON documents.chunks USING gin (tsv);
CREATE INDEX chunks_set_doc   ON documents.chunks (doc_set_id, document_id);

-- -----------------------------------------------------------------------------
-- qa: hội thoại, lượt hỏi đáp, trích dẫn, đánh giá (DE-QA, DE-FBA)
-- -----------------------------------------------------------------------------
CREATE TABLE qa.conversations (
    id          uuid        PRIMARY KEY,
    user_id     uuid        NOT NULL REFERENCES access.users(id) ON DELETE CASCADE,
    doc_set_id  uuid        NOT NULL REFERENCES documents.doc_sets(id) ON DELETE CASCADE,
    created_at  timestamptz NOT NULL DEFAULT now(),
    closed_at   timestamptz                                                   -- UC-16
);
CREATE INDEX conversations_user_idx    ON qa.conversations (user_id, created_at DESC);
CREATE INDEX conversations_created_idx ON qa.conversations (created_at);      -- retention 30 ngày (BRU-003)

CREATE TABLE qa.turns (
    id                    uuid        PRIMARY KEY,
    conversation_id       uuid        NOT NULL REFERENCES qa.conversations(id) ON DELETE CASCADE,
    turn_index            integer     NOT NULL CHECK (turn_index >= 0),
    question              text        NOT NULL CHECK (char_length(question) BETWEEN 1 AND 2000),
    standalone_question   text,                                               -- UC-11
    lang                  text        NOT NULL CHECK (lang IN ('vi', 'en')),
    answer                text,
    answer_type           text        CHECK (answer_type IN ('answered','not_found','clarification')),
    status                text        NOT NULL CHECK (status IN ('completed','stopped','incomplete')),  -- SAD §3.3
    error_code            text        CHECK (error_code IN ('AI_UNAVAILABLE','AI_TIMEOUT','AI_REFUSED','MAX_TOKENS','NETWORK','INTERNAL')),
    pending_document_ids  uuid[]      NOT NULL DEFAULT '{}',                  -- AC-US001-3
    latency_first_ms      integer,
    latency_total_ms      integer,
    created_at            timestamptz NOT NULL DEFAULT now(),
    UNIQUE (conversation_id, turn_index),
    CHECK ((status = 'completed') = (answer_type IS NOT NULL)),
    CHECK ((status = 'incomplete') = (error_code IS NOT NULL))
);

CREATE TABLE qa.citations (
    id           uuid     PRIMARY KEY,
    turn_id      uuid     NOT NULL REFERENCES qa.turns(id) ON DELETE CASCADE,
    idx          smallint NOT NULL CHECK (idx >= 1),
    chunk_id     uuid     REFERENCES documents.chunks(id) ON DELETE SET NULL,
    document_id  uuid     NOT NULL,                                           -- không FK: còn lại sau khi gỡ
    filename     text,                                                        -- NULL sau khi gỡ (DD-09)
    page         integer  NOT NULL CHECK (page >= 1),
    snippet      text     CHECK (char_length(snippet) <= 300),                -- AC-US009-2; NULL sau khi gỡ
    removed      boolean  NOT NULL DEFAULT false,
    UNIQUE (turn_id, idx),
    CHECK (NOT removed OR (snippet IS NULL AND filename IS NULL))
);
CREATE INDEX citations_document_idx ON qa.citations (document_id);           -- dùng khi gỡ tài liệu

CREATE TABLE qa.feedback (                                                    -- UC-17
    turn_id     uuid        NOT NULL REFERENCES qa.turns(id) ON DELETE CASCADE,
    user_id     uuid        NOT NULL REFERENCES access.users(id) ON DELETE CASCADE,
    rating      text        NOT NULL CHECK (rating IN ('up', 'down')),
    reason      text        CHECK (reason IN ('wrong','incomplete','wrong_source','other')),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (turn_id, user_id),
    CHECK (rating = 'down' OR reason IS NULL)
);

-- -----------------------------------------------------------------------------
-- audit: nhật ký truy cập append-only, phân vùng theo tháng (DE-AUD, NFR-010, BRU-004)
-- -----------------------------------------------------------------------------
CREATE TABLE audit.audit_log (
    id           bigint GENERATED ALWAYS AS IDENTITY,
    ts           timestamptz NOT NULL DEFAULT now(),
    user_id      uuid,
    action       text        NOT NULL CHECK (action IN (
                    'login','logout','session_expired','classification_confirm',
                    'upload','view_list','view_citation','view_file','query',
                    'remove_document','member_add','member_remove','role_change',
                    'audit_query','audit_export','access_denied')),
    doc_set_id   uuid,
    document_id  uuid,
    meta         jsonb       NOT NULL DEFAULT '{}'::jsonb,                    -- KHÔNG chứa nội dung (G-13)
    PRIMARY KEY (id, ts)
) PARTITION BY RANGE (ts);
CREATE INDEX audit_set_ts_idx  ON audit.audit_log (doc_set_id, ts);
CREATE INDEX audit_user_ts_idx ON audit.audit_log (user_id, ts);
-- Ví dụ phân vùng; job retention tạo trước phân vùng tháng kế tiếp và drop phân vùng > 12 tháng.
CREATE TABLE audit.audit_log_2026_11 PARTITION OF audit.audit_log FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE audit.audit_log_2026_12 PARTITION OF audit.audit_log FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE audit.audit_log_2027_01 PARTITION OF audit.audit_log FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');

-- -----------------------------------------------------------------------------
-- analytics: sự kiện sản phẩm EVT-001..016 (DE-FBA, IF-03)
-- -----------------------------------------------------------------------------
CREATE TABLE analytics.events (
    id            bigint GENERATED ALWAYS AS IDENTITY,
    ts            timestamptz NOT NULL DEFAULT now(),
    name          text        NOT NULL,
    anon_user_id  bytea       NOT NULL,                                       -- HMAC-SHA256(user_id)
    session_id    bytea,
    doc_set_id    uuid,
    props         jsonb       NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (id, ts)
) PARTITION BY RANGE (ts);
CREATE INDEX events_name_ts_idx ON analytics.events (name, ts);
CREATE TABLE analytics.events_2026_11 PARTITION OF analytics.events FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE analytics.events_2026_12 PARTITION OF analytics.events FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');
CREATE TABLE analytics.events_2027_01 PARTITION OF analytics.events FOR VALUES FROM ('2027-01-01') TO ('2027-02-01');

-- -----------------------------------------------------------------------------
-- billing: giới hạn tần suất, sổ chi phí, ngân sách (DE-BIL, G-16)
-- -----------------------------------------------------------------------------
CREATE TABLE billing.price_table (
    model                   text   NOT NULL,
    input_usd_micros_mtok   bigint NOT NULL,   -- USD × 10^6 cho 1 triệu token đầu vào
    output_usd_micros_mtok  bigint NOT NULL,
    cache_read_usd_micros_mtok bigint NOT NULL DEFAULT 0,
    effective_from          date   NOT NULL,
    PRIMARY KEY (model, effective_from)
);

CREATE TABLE billing.usage_ledger (
    id                 bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ts                 timestamptz NOT NULL DEFAULT now(),
    turn_id            uuid,
    document_id        uuid,
    purpose            text   NOT NULL CHECK (purpose IN ('rewrite','answer','embed_query','embed_document')),
    model              text   NOT NULL,
    input_tokens       integer NOT NULL DEFAULT 0,
    output_tokens      integer NOT NULL DEFAULT 0,
    cache_read_tokens  integer NOT NULL DEFAULT 0,
    cost_usd_micros    bigint  NOT NULL
);
CREATE INDEX usage_ts_idx ON billing.usage_ledger (ts);

CREATE TABLE billing.rate_window (
    user_id       uuid        NOT NULL REFERENCES access.users(id) ON DELETE CASCADE,
    window_start  timestamptz NOT NULL,                                       -- date_trunc('hour', now())
    count         integer     NOT NULL,
    PRIMARY KEY (user_id, window_start)
);

CREATE TABLE billing.monthly_budget (
    month            date    PRIMARY KEY,                                     -- ngày 1 của tháng
    cap_usd_micros   bigint  NOT NULL,                                        -- 5 triệu VND quy đổi [GĐ]
    spent_usd_micros bigint  NOT NULL DEFAULT 0,
    alert_sent_at    timestamptz,                                             -- cảnh báo 80%
    blocked          boolean NOT NULL DEFAULT false                           -- chặn ở 100%
);

-- -----------------------------------------------------------------------------
-- Row-Level Security: lớp phòng thủ thứ hai cho nội dung (SAD §3.1, BRU-007)
-- Ứng dụng đặt: SET LOCAL app.doc_set_ids = '<uuid>,<uuid>' ở đầu mỗi transaction.
-- Không đặt → current_setting trả NULL → không thấy dòng nào (từ chối mặc định).
-- -----------------------------------------------------------------------------
ALTER TABLE documents.chunks    ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents.chunks    FORCE  ROW LEVEL SECURITY;
CREATE POLICY chunks_by_doc_set ON documents.chunks
    USING (doc_set_id = ANY (string_to_array(current_setting('app.doc_set_ids', true), ',')::uuid[]))
    WITH CHECK (doc_set_id = ANY (string_to_array(current_setting('app.doc_set_ids', true), ',')::uuid[]));

ALTER TABLE qa.citations ENABLE ROW LEVEL SECURITY;
ALTER TABLE qa.citations FORCE  ROW LEVEL SECURITY;
CREATE POLICY citations_by_owner ON qa.citations
    USING (EXISTS (SELECT 1 FROM qa.turns t JOIN qa.conversations c ON c.id = t.conversation_id
                   WHERE t.id = qa.citations.turn_id
                     AND c.doc_set_id = ANY (string_to_array(current_setting('app.doc_set_ids', true), ',')::uuid[])));

-- -----------------------------------------------------------------------------
-- Vai trò CSDL (quyền tối thiểu). Mật khẩu do Secrets Manager quản lý, không nằm ở đây.
-- -----------------------------------------------------------------------------
-- cwd_api:       đọc/ghi access, documents.documents, qa, billing; INSERT/SELECT audit, analytics.
-- cwd_worker:    cập nhật documents.documents (trạng thái), ghi documents.chunks, INSERT analytics, billing.usage_ledger.
-- cwd_retention: BYPASSRLS; DELETE theo BRU-002..004; DROP/CREATE phân vùng audit, analytics.
-- cwd_readonly:  (Metabase) SELECT trên analytics và các view tổng hợp; KHÔNG có quyền trên documents.chunks, qa.turns, qa.citations.
-- Ví dụ quyền bất biến của nhật ký:
--   REVOKE UPDATE, DELETE ON audit.audit_log FROM cwd_api;
--   GRANT INSERT, SELECT ON audit.audit_log TO cwd_api;
