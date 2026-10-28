import { useMutation } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { purgeDocument } from "../../api/admin";
import type { AdminDocument } from "../../api/types";
import { formatDateTime } from "../../format";
import { Icon } from "../Icon";
import { Modal } from "../Modal";

/** Hộp xác nhận gỡ (màn 09): focus mặc định ở Hủy; "Gỡ vĩnh viễn" chỉ bật khi đủ 2 ô và đã tích. */
export function PurgeDialog({
  doc,
  onClose,
  onPurged,
}: {
  doc: AdminDocument;
  onClose: () => void;
  onPurged: () => void;
}) {
  const [requestedBy, setRequestedBy] = useState("");
  const [reason, setReason] = useState("");
  const [understood, setUnderstood] = useState(false);
  const cancel = useRef<HTMLButtonElement>(null);
  const purge = useMutation({
    mutationFn: () => purgeDocument(doc.id, requestedBy.trim(), reason.trim()),
    onSuccess: onPurged,
  });
  const ready = requestedBy.trim() !== "" && reason.trim() !== "" && understood && !purge.isPending;

  return (
    <Modal
      titleId="pg-title"
      descriptionId="pg-desc"
      role="alertdialog"
      initialFocus={cancel}
      onClose={onClose}
      onSubmit={() => ready && purge.mutate()}
    >
      <div className="dialog-header">
        <div className="dialog-icon danger">
          <Icon name="trash" />
        </div>
        <div>
          <h2 id="pg-title">Gỡ hoàn toàn tài liệu?</h2>
          <p id="pg-desc" className="muted small">
            Thao tác <strong>không hoàn tác được</strong>. File gốc, nội dung đã xử lý và các đoạn trích trong lịch sử hội
            thoại đều bị xóa.
          </p>
        </div>
      </div>
      <div className="dialog-body">
        <dl className="meta-grid">
          <dt>Tên file</dt>
          <dd>{doc.filename}</dd>
          <dt>Người tải lên</dt>
          <dd>
            {doc.uploaded_by_email} · {formatDateTime(doc.uploaded_at)}
          </dd>
        </dl>
        <div className="field">
          <label htmlFor="pg-by">
            Người yêu cầu gỡ <span aria-hidden="true">*</span>
          </label>
          <input
            id="pg-by"
            className="input"
            required
            maxLength={200}
            value={requestedBy}
            onChange={(e) => setRequestedBy(e.target.value)}
          />
          <span className="field-hint">Trưởng nhóm BD hoặc Pháp chế</span>
        </div>
        <div className="field">
          <label htmlFor="pg-reason">
            Lý do <span aria-hidden="true">*</span>
          </label>
          <textarea
            id="pg-reason"
            className="textarea"
            rows={3}
            required
            maxLength={500}
            value={reason}
            onChange={(e) => setReason(e.target.value)}
          />
          <span className="field-hint">Ghi vào nhật ký truy cập; không lưu nội dung tài liệu.</span>
        </div>
        <label className="checkbox">
          <input type="checkbox" checked={understood} onChange={(e) => setUnderstood(e.target.checked)} />
          <span>Tôi hiểu tài liệu sẽ bị xóa vĩnh viễn khỏi công cụ.</span>
        </label>
        {purge.isError && <p className="field-error">Không gỡ được tài liệu. Hãy thử lại.</p>}
      </div>
      <div className="dialog-footer">
        <button ref={cancel} className="btn btn-secondary" type="button" onClick={onClose}>
          Hủy
        </button>
        <button className="btn btn-danger" type="submit" disabled={!ready}>
          <Icon name="trash" small />
          Gỡ vĩnh viễn
        </button>
      </div>
    </Modal>
  );
}
