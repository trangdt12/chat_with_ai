import type { DocumentOut } from "../api/types";
import { documentErrorMessage, statusLabel } from "./documentMessages";
import { Icon } from "./Icon";

const BADGE: Record<DocumentOut["status"], { cls: string; text: string }> = {
  uploaded: { cls: "badge-neutral", text: "Đã tải lên" },
  processing: { cls: "badge-processing", text: "Đang xử lý" },
  ready: { cls: "badge-ready", text: "Sẵn sàng" },
  failed: { cls: "badge-failed", text: "Lỗi" },
};

function shortDate(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export function DocumentRow({ doc }: { doc: DocumentOut }) {
  const badge = BADGE[doc.status];
  const pages = doc.pages != null ? `${doc.pages} trang · ` : "";
  return (
    <li className="doc-row">
      {doc.status === "failed" ? (
        <span style={{ color: "var(--c-danger-700)" }}>
          <Icon name="x-circle" />
        </span>
      ) : (
        <Icon name="file" />
      )}
      <div>
        <div className="doc-name">{doc.filename}</div>
        {doc.status === "failed" ? (
          <div className="doc-error">{documentErrorMessage(doc.error_code, doc.filename)}</div>
        ) : (
          <div className="doc-meta">
            {pages}
            {doc.status === "ready" ? shortDate(doc.uploaded_at) : statusLabel(doc.status, doc.progress)}
          </div>
        )}
        {doc.status === "processing" && (
          <div
            className="progress"
            role="progressbar"
            aria-valuenow={doc.progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Tiến trình xử lý ${doc.filename}`}
          >
            <span style={{ width: `${doc.progress}%` }} />
          </div>
        )}
      </div>
      <span className={`badge ${badge.cls}`}>{badge.text}</span>
    </li>
  );
}

/** Dòng tạm khi file đang được gửi lên server. */
export function UploadingRow({ name, percent, retry }: { name: string; percent: number; retry: number }) {
  return (
    <li className="doc-row">
      <Icon name="loader" className="spin" />
      <div>
        <div className="doc-name">{name}</div>
        <div className="doc-meta">
          {retry > 0 ? `Mất kết nối, đang thử lại… (${retry}/3)` : `Đang tải lên ${percent}%`}
        </div>
        <div
          className="progress"
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Tải lên ${name}`}
        >
          <span style={{ width: `${percent}%`, background: "var(--c-primary-600)" }} />
        </div>
      </div>
      <span className="badge badge-info">Đang tải</span>
    </li>
  );
}
