import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useDeferredValue, useState } from "react";
import { adminDocuments } from "../../api/admin";
import type { AdminDocument } from "../../api/types";
import { formatDateTime, formatMB } from "../../format";
import { Icon } from "../Icon";
import { useToast } from "../Toasts";
import { PurgeDialog } from "./PurgeDialog";

const STATUS: Record<AdminDocument["status"], { cls: string; text: string }> = {
  uploaded: { cls: "badge-neutral", text: "Đã tải lên" },
  processing: { cls: "badge-processing", text: "Đang xử lý" },
  ready: { cls: "badge-ready", text: "Sẵn sàng" },
  failed: { cls: "badge-failed", text: "Lỗi" },
};

/** Màn 09: chỉ thông tin mô tả (BRU-007) + gỡ hoàn toàn (US-020). */
export function DocumentsTab({ docSetId, docSetName }: { docSetId: string; docSetName: string }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [q, setQ] = useState("");
  const query = useDeferredValue(q.trim());
  const docs = useQuery({
    queryKey: ["admin", "documents", docSetId, query],
    queryFn: () => adminDocuments(docSetId, query),
  });
  const [target, setTarget] = useState<AdminDocument | null>(null);

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Gỡ tài liệu · {docSetName}</h1>
          <p className="muted">Gỡ hoàn toàn theo yêu cầu của Trưởng nhóm BD hoặc Pháp chế.</p>
        </div>
      </div>
      <div className="banner banner-info" style={{ marginBottom: "var(--sp-4)" }}>
        <Icon name="shield" />
        <div>Bạn chỉ thấy thông tin mô tả của tài liệu, không xem được nội dung.</div>
      </div>
      <div className="search">
        <Icon name="search" />
        <label htmlFor="doc-q" className="sr-only">
          Tìm theo tên file
        </label>
        <input
          id="doc-q"
          className="input"
          type="search"
          placeholder="Tìm theo tên file…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {docs.isPending ? (
        <div className="stack" aria-busy="true">
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      ) : docs.isError ? (
        <p className="field-error">Không tải được danh sách tài liệu.</p>
      ) : docs.data.length === 0 ? (
        <p className="muted">{query ? "Không có tài liệu nào khớp tên đã nhập." : "Bộ tài liệu chưa có tài liệu nào."}</p>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <caption className="sr-only">Tài liệu trong bộ {docSetName} (chỉ thông tin mô tả)</caption>
            <thead>
              <tr>
                <th scope="col">Tên file</th>
                <th scope="col">Số trang</th>
                <th scope="col">Dung lượng</th>
                <th scope="col">Người tải lên</th>
                <th scope="col">Thời điểm</th>
                <th scope="col">Trạng thái</th>
                <th scope="col">
                  <span className="sr-only">Thao tác</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {docs.data.map((d) => (
                <tr key={d.id}>
                  <td>
                    <strong>{d.filename}</strong>
                  </td>
                  <td>{d.pages ?? "—"}</td>
                  <td>{formatMB(d.size_bytes)}</td>
                  <td>{d.uploaded_by_email}</td>
                  <td>{formatDateTime(d.uploaded_at)}</td>
                  <td>
                    <span className={`badge ${STATUS[d.status].cls}`}>{STATUS[d.status].text}</span>
                  </td>
                  <td>
                    <button
                      className="btn btn-ghost btn-sm"
                      type="button"
                      style={{ color: "var(--c-danger-700)" }}
                      aria-label={`Gỡ ${d.filename}`}
                      onClick={() => setTarget(d)}
                    >
                      <Icon name="trash" small />
                      Gỡ
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {target && (
        <PurgeDialog
          doc={target}
          onClose={() => setTarget(null)}
          onPurged={() => {
            const name = target.filename;
            setTarget(null);
            qc.invalidateQueries({ queryKey: ["admin", "documents", docSetId] });
            toast(`Đã gỡ ${name}. Tài liệu đã biến khỏi danh sách của mọi người dùng. Đã ghi nhật ký.`, "success");
          }}
        />
      )}
    </>
  );
}
