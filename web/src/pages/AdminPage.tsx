import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { adminDocSets } from "../api/admin";
import { AppHeader } from "../components/AppHeader";
import { AuditTab } from "../components/admin/AuditTab";
import { DocumentsTab } from "../components/admin/DocumentsTab";
import { MembersTab } from "../components/admin/MembersTab";
import { Icon, type IconName } from "../components/Icon";

const STORAGE_KEY = "cwd.admin.docSet";

type Tab = "members" | "documents" | "audit";
const TABS: { id: Tab; label: string; icon: IconName }[] = [
  { id: "members", label: "Nhóm truy cập", icon: "users" },
  { id: "documents", label: "Gỡ tài liệu", icon: "trash" },
  { id: "audit", label: "Nhật ký truy cập", icon: "list" },
];

function readStored(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStored(id: string) {
  try {
    localStorage.setItem(STORAGE_KEY, id);
  } catch {
    // localStorage bị chặn — chỉ mất tiện ích nhớ lựa chọn
  }
}

/** Trang quản trị: không có liên kết nào sang "/" hay tới nội dung tài liệu (AC-US021-5). */
export function AdminPage() {
  const [params, setParams] = useSearchParams();
  const tab = (TABS.some((t) => t.id === params.get("tab")) ? params.get("tab") : "members") as Tab;
  const docSets = useQuery({ queryKey: ["admin", "doc-sets"], queryFn: adminDocSets });
  const [docSetId, setDocSetId] = useState<string | null>(readStored);

  useEffect(() => {
    const list = docSets.data;
    if (list?.length && !list.some((d) => d.id === docSetId)) setDocSetId(list[0].id);
  }, [docSets.data, docSetId]);

  const current = docSets.data?.find((d) => d.id === docSetId) ?? null;

  function chooseDocSet(id: string) {
    setDocSetId(id);
    writeStored(id);
  }

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Bỏ qua tới nội dung chính
      </a>
      <AppHeader homeHref="/admin" showAdminLink={false} docSetName="Quản trị" />
      <div className="admin">
        <nav className="admin-nav" aria-label="Quản trị">
          <div className="field" style={{ padding: "0 var(--sp-3) var(--sp-3)" }}>
            <label htmlFor="admin-docset">Bộ tài liệu</label>
            <select
              id="admin-docset"
              className="select"
              value={docSetId ?? ""}
              onChange={(e) => chooseDocSet(e.target.value)}
              disabled={!docSets.data?.length}
            >
              {docSets.data?.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.member_count} thành viên)
                </option>
              ))}
            </select>
          </div>
          {TABS.map((t) => (
            <a
              key={t.id}
              href={`?tab=${t.id}`}
              aria-current={tab === t.id ? "page" : undefined}
              onClick={(e) => {
                e.preventDefault();
                setParams({ tab: t.id });
              }}
            >
              <Icon name={t.icon} />
              {t.label}
            </a>
          ))}
        </nav>
        <main className="admin-main" id="main">
          {docSets.isPending ? (
            <div className="skeleton" />
          ) : docSets.isError ? (
            <p className="field-error">Không tải được danh sách bộ tài liệu.</p>
          ) : !current ? (
            <p className="muted">Chưa có bộ tài liệu nào.</p>
          ) : tab === "members" ? (
            <MembersTab key={current.id} docSetId={current.id} docSetName={current.name} />
          ) : tab === "documents" ? (
            <DocumentsTab key={current.id} docSetId={current.id} docSetName={current.name} />
          ) : (
            <AuditTab key={current.id} docSetId={current.id} />
          )}
        </main>
      </div>
    </div>
  );
}
