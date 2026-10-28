import { useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { auditLogs, listMembers, type AuditFilters } from "../../api/admin";
import type { AuditItem } from "../../api/types";
import { useCurrentMe } from "../../auth/useMe";
import { ROLE_LABELS, formatDateTime, formatMB, isoDate } from "../../format";
import { Icon } from "../Icon";
import { membersKey } from "./MembersTab";

export const ACTION_LABELS: Record<string, string> = {
  login: "Đăng nhập",
  classification_confirm: "Xác nhận phân loại",
  upload: "Tải lên",
  query: "Hỏi đáp",
  view_citation: "Xem trích dẫn",
  view_file: "Mở tài liệu gốc",
  view_list: "Xem danh sách tài liệu",
  member_add: "Thêm thành viên",
  member_remove: "Gỡ thành viên",
  role_change: "Đổi vai trò",
  remove_document: "Gỡ tài liệu",
};

const BADGE: Record<string, string> = {
  remove_document: "badge-failed",
  member_remove: "badge-failed",
  query: "badge-info",
};

const ANSWER_TYPE: Record<string, string> = {
  answered: "đã trả lời",
  not_found: "không tìm thấy",
  clarification: "cần làm rõ",
};

const roleLabel = (r: unknown) => ROLE_LABELS[r as keyof typeof ROLE_LABELS] ?? String(r);

/** Ghi chú dựng từ meta: lý do gỡ, số trang, vai trò… Không bao giờ có câu hỏi hay đoạn văn. */
export function auditNote(item: AuditItem, people: Map<string, string>): string {
  const m = item.meta ?? {};
  const target = typeof m.target_user_id === "string" ? (people.get(m.target_user_id) ?? "") : "";
  switch (item.action) {
    case "remove_document":
      return [`Yêu cầu: ${m.requested_by}`, `“${m.reason}”`, m.pages ? `${m.pages} trang` : ""].filter(Boolean).join(" · ");
    case "query": {
      const parts = [`${m.citation_count ?? 0} nguồn trích dẫn`];
      if (m.answer_type) parts.push(ANSWER_TYPE[String(m.answer_type)] ?? String(m.answer_type));
      if (m.status && m.status !== "completed") parts.push(m.status === "stopped" ? "đã dừng" : "gián đoạn");
      return parts.join(" · ");
    }
    case "upload":
      return typeof m.size_bytes === "number" ? formatMB(m.size_bytes) : "";
    case "member_add":
      return [target, roleLabel(m.role)].filter(Boolean).join(" · ");
    case "role_change":
      return [target, `${roleLabel(m.from)} → ${roleLabel(m.to)}`].filter(Boolean).join(" · ");
    case "member_remove":
      return target;
    default:
      return "";
  }
}

function defaultFilters(docSetId: string): AuditFilters {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - 6);
  return { docSetId, from: isoDate(from), to: isoDate(to), userId: "", action: "" };
}

/** Màn 10: tra cứu nhật ký truy cập (US-022). Không có xuất CSV ở bản thử nghiệm. */
export function AuditTab({ docSetId }: { docSetId: string }) {
  const me = useCurrentMe();
  const [draft, setDraft] = useState(() => defaultFilters(docSetId));
  const [applied, setApplied] = useState(draft);
  const [cursors, setCursors] = useState<(string | null)[]>([null]); // ngăn xếp cursor để quay lại trang trước
  const cursor = cursors[cursors.length - 1];

  const members = useQuery({ queryKey: membersKey(docSetId), queryFn: () => listMembers(docSetId) });
  const people = new Map<string, string>([[me.user_id, me.email]]);
  for (const m of members.data ?? []) people.set(m.user_id, m.email);

  const page = useQuery({
    queryKey: ["admin", "audit", applied, cursor],
    queryFn: () => auditLogs(applied, cursor),
  });

  function submit(e: FormEvent) {
    e.preventDefault();
    setApplied({ ...draft });
    setCursors([null]);
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Nhật ký truy cập</h1>
          <p className="muted">
            Ai đã xem, hỏi hay thay đổi bộ tài liệu, vào lúc nào. Không chứa nội dung tài liệu hay câu hỏi.
          </p>
        </div>
      </div>
      <form className="filters" onSubmit={submit} aria-label="Bộ lọc nhật ký">
        <div className="field">
          <label htmlFor="f-from">Từ ngày</label>
          <input
            id="f-from"
            className="input"
            type="date"
            value={draft.from}
            max={draft.to}
            onChange={(e) => setDraft({ ...draft, from: e.target.value })}
          />
        </div>
        <div className="field">
          <label htmlFor="f-to">Đến ngày</label>
          <input
            id="f-to"
            className="input"
            type="date"
            value={draft.to}
            min={draft.from}
            onChange={(e) => setDraft({ ...draft, to: e.target.value })}
          />
        </div>
        <div className="field">
          <label htmlFor="f-user">Người dùng</label>
          <select
            id="f-user"
            className="select"
            value={draft.userId}
            onChange={(e) => setDraft({ ...draft, userId: e.target.value })}
          >
            <option value="">Tất cả</option>
            {(members.data ?? []).map((m) => (
              <option key={m.user_id} value={m.user_id}>
                {m.display_name}
              </option>
            ))}
            {!members.data?.some((m) => m.user_id === me.user_id) && (
              <option value={me.user_id}>{me.display_name} (quản trị viên)</option>
            )}
          </select>
        </div>
        <div className="field">
          <label htmlFor="f-act">Thao tác</label>
          <select
            id="f-act"
            className="select"
            value={draft.action}
            onChange={(e) => setDraft({ ...draft, action: e.target.value })}
          >
            <option value="">Tất cả</option>
            {Object.entries(ACTION_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        <span />
        <button className="btn btn-primary" type="submit">
          <Icon name="search" small />
          Tra cứu
        </button>
      </form>

      {page.isPending ? (
        <div className="stack" aria-busy="true">
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      ) : page.isError ? (
        <p className="field-error">Không tải được nhật ký. Hãy thử lại.</p>
      ) : page.data.items.length === 0 ? (
        <section className="empty" aria-labelledby="em-title" style={{ marginTop: "var(--sp-6)" }}>
          <div className="empty-illus">
            <Icon name="info" />
          </div>
          <h2 id="em-title">Không có bản ghi nào khớp bộ lọc</h2>
          <p className="muted">Thử mở rộng khoảng thời gian hoặc chọn “Tất cả” ở Người dùng và Thao tác.</p>
        </section>
      ) : (
        <>
          <div className="table-wrap">
            <table className="table">
              <caption className="sr-only">Bản ghi nhật ký truy cập</caption>
              <thead>
                <tr>
                  <th scope="col">Thời điểm</th>
                  <th scope="col">Người dùng</th>
                  <th scope="col">Thao tác</th>
                  <th scope="col">Tài liệu</th>
                  <th scope="col">Ghi chú</th>
                </tr>
              </thead>
              <tbody>
                {page.data.items.map((it) => (
                  <tr key={it.id}>
                    <td>{formatDateTime(it.ts)}</td>
                    <td>{it.user_email ?? "—"}</td>
                    <td>
                      <span className={`badge ${BADGE[it.action] ?? "badge-neutral"}`}>
                        {ACTION_LABELS[it.action] ?? it.action}
                      </span>
                    </td>
                    <td>{it.document_filename ?? "—"}</td>
                    <td className="muted">{auditNote(it, people)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <span className="muted">
              Trang {cursors.length} · {page.data.items.length} bản ghi
            </span>
            <span className="row">
              <button
                className="btn btn-secondary btn-sm"
                type="button"
                disabled={cursors.length === 1}
                onClick={() => setCursors((cs) => cs.slice(0, -1))}
              >
                Trước
              </button>
              <button
                className="btn btn-secondary btn-sm"
                type="button"
                disabled={!page.data.next_cursor}
                onClick={() => setCursors((cs) => [...cs, page.data!.next_cursor])}
              >
                Sau
              </button>
            </span>
          </div>
        </>
      )}
    </>
  );
}
