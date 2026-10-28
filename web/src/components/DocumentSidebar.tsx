import type { DocumentOut } from "../api/types";
import type { UploadingFile } from "../hooks/useUpload";
import { DocumentRow, UploadingRow } from "./DocumentRow";
import { Icon } from "./Icon";
import { UploadDropzone } from "./UploadDropzone";

type Props = {
  documents: DocumentOut[];
  loading: boolean;
  uploading: UploadingFile[];
  canBatch: boolean;
  onFiles: (files: File[]) => void;
  onNewConversation: () => void;
  newConversationDisabled?: boolean;
  open: boolean;
};

/** UI-001: danh sách tài liệu mới nhất trước + vùng kéo thả + nút "Hội thoại mới". */
export function DocumentSidebar(props: Props) {
  const { documents, loading, uploading } = props;
  return (
    <aside className={`docs-panel${props.open ? " is-open" : ""}`} aria-labelledby="docs-title" id="docs-panel">
      <div className="docs-panel-header">
        <h2 id="docs-title">
          Tài liệu <span className="muted">({documents.length})</span>
        </h2>
      </div>
      <UploadDropzone canBatch={props.canBatch} onFiles={props.onFiles} disabled={uploading.length > 0} />

      {!loading && documents.length === 0 && uploading.length === 0 && (
        <p className="muted small" style={{ padding: "0 var(--sp-4)" }}>
          Chưa có tài liệu nào trong bộ này.
        </p>
      )}
      {loading && (
        <div className="stack" style={{ padding: "0 var(--sp-4)" }} aria-busy="true">
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      )}

      <ul className="doc-list" aria-live="polite" aria-label="Danh sách tài liệu, mới nhất trước">
        {uploading.map((u) => (
          <UploadingRow key={`up-${u.name}`} name={u.name} percent={u.percent} retry={u.retry} />
        ))}
        {documents.map((d) => (
          <DocumentRow key={d.id} doc={d} />
        ))}
      </ul>

      <div className="docs-panel-footer">
        <button
          className="btn btn-secondary btn-sm"
          type="button"
          onClick={props.onNewConversation}
          disabled={props.newConversationDisabled}
        >
          <Icon name="plus" small />
          Hội thoại mới
        </button>
      </div>
    </aside>
  );
}
