import type { DocumentOut, UploadResult } from "../api/types";
import { ERROR_ACTIONS, documentErrorMessage } from "./documentMessages";
import { Icon } from "./Icon";

export type BatchRun = { startedAt: Date; results: UploadResult[]; rejected: { name: string; code: string }[] };

type Row = { name: string; code: string };

/** Kết quả tải lô cho Quản lý bộ tài liệu (màn 04 #manager); số liệu tự cập nhật theo polling danh sách. */
export function BatchResultPanel({
  batch,
  documents,
  onClose,
}: {
  batch: BatchRun;
  documents: DocumentOut[];
  onClose: () => void;
}) {
  const byId = new Map(documents.map((d) => [d.id, d]));
  const accepted = batch.results.filter((r) => r.id);
  const docs = accepted.map((r) => byId.get(r.id!)).filter((d): d is DocumentOut => !!d);
  const ready = docs.filter((d) => d.status === "ready").length;
  const processing = docs.filter((d) => d.status === "uploaded" || d.status === "processing").length;
  const failedDocs = docs.filter((d) => d.status === "failed");
  const refused: Row[] = [
    ...batch.rejected,
    ...batch.results.filter((r) => r.error_code).map((r) => ({ name: r.filename, code: r.error_code! })),
  ];
  const needAction: Row[] = [
    ...failedDocs.map((d) => ({ name: d.filename, code: d.error_code ?? "corrupt" })),
    ...refused,
  ];
  const full = refused.find((r) => r.code === "DOC_SET_FULL");
  const total = batch.results.length + batch.rejected.length;
  const time = batch.startedAt.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

  return (
    <section className="batch card" aria-labelledby="batch-title">
      <div className="card-body">
        <div className="page-head" style={{ marginBottom: 0 }}>
          <div>
            <h1 id="batch-title">Kết quả tải lô · {total} file</h1>
            <p className="muted small">Bắt đầu {time} · Danh sách bên trái cập nhật tự động</p>
          </div>
          <button className="btn btn-ghost btn-icon btn-sm" type="button" aria-label="Đóng kết quả tải lô" onClick={onClose}>
            <Icon name="x" small />
          </button>
        </div>
        <div className="batch-stats">
          <Stat value={ready} label="Sẵn sàng" color="var(--c-success-700)" />
          <Stat value={processing} label="Đang xử lý" color="var(--c-warning-700)" />
          <Stat value={failedDocs.length} label="Lỗi khi xử lý" color="var(--c-danger-700)" />
          <Stat value={refused.length} label="Bị từ chối" color="var(--c-neutral-700)" />
        </div>
        {full && (
          <div className="banner banner-warning">
            <Icon name="alert" />
            <div>
              <strong className="banner-title">Bộ tài liệu đã đạt tối đa 50 file</strong>
              {documentErrorMessage("DOC_SET_FULL", full.name)}
            </div>
          </div>
        )}
        {needAction.length > 0 && (
          <div className="table-wrap" style={{ marginTop: "var(--sp-4)" }}>
            <table className="table">
              <caption className="sr-only">File cần xử lý</caption>
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col">Kết quả</th>
                  <th scope="col">Việc cần làm</th>
                </tr>
              </thead>
              <tbody>
                {needAction.map((row, i) => {
                  const info = ERROR_ACTIONS[row.code] ?? { label: "Lỗi", action: "Thử tải lại" };
                  const refusedRow = row.code === row.code.toUpperCase();
                  return (
                    <tr key={`${row.name}-${i}`}>
                      <td>{row.name}</td>
                      <td>
                        <span className={`badge ${refusedRow ? "badge-neutral" : "badge-failed"}`}>{info.label}</span>
                      </td>
                      <td>{info.action}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

function Stat({ value, label, color }: { value: number; label: string; color: string }) {
  return (
    <div className="stat">
      <div className="stat-num" style={{ color }}>
        {value}
      </div>
      <div className="small muted">{label}</div>
    </div>
  );
}
