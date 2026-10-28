import { apiFetch, jsonBody } from "./client";
import type { AdminDocSet, AdminDocument, AuditPage, Member, Role } from "./types";

export const adminDocSets = () => apiFetch<AdminDocSet[]>("/admin/doc-sets");

export const listMembers = (dsid: string) => apiFetch<Member[]>(`/admin/doc-sets/${dsid}/members`);

export const addMember = (dsid: string, email: string, role: Role) =>
  apiFetch<Member>(`/admin/doc-sets/${dsid}/members`, { method: "POST", ...jsonBody({ email, role }) });

export const changeRole = (dsid: string, uid: string, role: Role) =>
  apiFetch<Member>(`/admin/doc-sets/${dsid}/members/${uid}`, { method: "PATCH", ...jsonBody({ role }) });

export const removeMember = (dsid: string, uid: string) =>
  apiFetch<void>(`/admin/doc-sets/${dsid}/members/${uid}`, { method: "DELETE" });

export const adminDocuments = (dsid: string, q: string) =>
  apiFetch<AdminDocument[]>(`/admin/doc-sets/${dsid}/documents${q ? `?q=${encodeURIComponent(q)}` : ""}`);

export const purgeDocument = (id: string, requestedBy: string, reason: string) =>
  apiFetch<{ id: string; removed: boolean }>(`/admin/documents/${id}`, {
    method: "DELETE",
    ...jsonBody({ requested_by: requestedBy, reason }),
  });

export type AuditFilters = { docSetId: string; from: string; to: string; userId: string; action: string };

export function auditLogs(f: AuditFilters, cursor: string | null, limit = 50): Promise<AuditPage> {
  const params = new URLSearchParams({ doc_set_id: f.docSetId, from: f.from, to: f.to, limit: String(limit) });
  if (f.userId) params.set("user_id", f.userId);
  if (f.action) params.set("action", f.action);
  if (cursor) params.set("cursor", cursor);
  return apiFetch<AuditPage>(`/admin/audit-logs?${params}`);
}
