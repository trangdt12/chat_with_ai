// Kiểu dữ liệu API, viết tay theo docs/implements/tasks/README.md §2.3.

export type Role = "member" | "manager";

export type DocSetRef = { id: string; name: string; role: Role };

export type Me = {
  user_id: string;
  email: string;
  display_name: string;
  is_admin: boolean;
  doc_sets: DocSetRef[];
};

export type DevUser = { email: string; display_name: string };

export type ApiErrorBody = { code: string; message: string };

// ---- Tài liệu (T-05, T-07) ----

export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

export type DocumentOut = {
  id: string;
  filename: string;
  pages: number | null;
  size_bytes: number;
  status: DocumentStatus;
  progress: number;
  error_code: string | null;
  uploaded_by: string;
  uploaded_at: string;
};

export type UploadResult = {
  filename: string;
  id: string | null;
  status: "uploaded" | null;
  error_code: string | null;
};

// ---- Hỏi đáp (T-10, T-11) ----

export type AnswerType = "answered" | "not_found" | "clarification";

export type CitationRef = {
  idx: number;
  citation_id: string;
  document_id: string | null;
  filename: string | null;
  page: number;
};

export type PendingDocument = { id: string; filename: string };

export type AnswerEvent =
  | { event: "answer.started"; data: { message_id: string; turn_index: number } }
  | { event: "answer.delta"; data: { text: string; citations: CitationRef[] } }
  | {
      event: "answer.completed";
      data: {
        message_id: string;
        answer_type: AnswerType;
        citations: CitationRef[];
        pending_documents: PendingDocument[];
      };
    }
  | { event: "answer.stopped"; data: { message_id: string } }
  | { event: "answer.failed"; data: { message_id?: string; code: string } };

export type CitationDetail = { document_id: string; filename: string; page: number; snippet: string };

export type Span = { text: string; citations: CitationRef[] };

export type TurnStatus = "streaming" | "completed" | "stopped" | "failed";

export type FeedbackRating = "up" | "down";
export type FeedbackReason = "wrong" | "missing" | "wrong_source" | "other";

export type Turn = {
  key: string; // id phía client, có trước message_id
  question: string;
  messageId: string | null;
  spans: Span[];
  status: TurnStatus;
  answerType: AnswerType | null;
  citations: CitationRef[];
  pendingDocuments: PendingDocument[];
  failCode: string | null;
  feedback: { rating: FeedbackRating; reason: FeedbackReason | null } | null;
};

// ---- Quản trị (T-13, T-14) ----

export type AdminDocSet = { id: string; name: string; member_count: number };

export type Member = {
  user_id: string;
  email: string;
  display_name: string;
  role: Role;
  granted_at: string;
};

export type AdminDocument = {
  id: string;
  filename: string;
  pages: number | null;
  size_bytes: number;
  status: DocumentStatus;
  error_code: string | null;
  uploaded_by_email: string;
  uploaded_at: string;
};

export type AuditItem = {
  id: number;
  ts: string;
  user_id: string | null;
  user_email: string | null;
  action: string;
  document_id: string | null;
  document_filename: string | null;
  meta: Record<string, unknown> | null;
};

export type AuditPage = { items: AuditItem[]; next_cursor: string | null };
