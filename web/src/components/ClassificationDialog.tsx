import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Icon } from "./Icon";

type Props = {
  filenames: string[];
  onConfirm: () => Promise<void> | void;
  onCancel: () => void;
};

/** Màn 03 — bắt buộc ở lần tải lên đầu tiên trong mỗi phiên (AC-US001-4). Esc = Hủy, focus nằm trong hộp thoại. */
export function ClassificationDialog({ filenames, onConfirm, onCancel }: Props) {
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const dialog = useRef<HTMLDivElement>(null);
  const checkbox = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    checkbox.current?.focus();
    return () => previous?.focus?.();
  }, []);

  function onKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      onCancel();
      return;
    }
    if (e.key !== "Tab" || !dialog.current) return;
    const focusable = Array.from(
      dialog.current.querySelectorAll<HTMLElement>("button:not([disabled]), input:not([disabled])"),
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  async function confirm() {
    setBusy(true);
    try {
      await onConfirm();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="overlay" onKeyDown={onKeyDown}>
      <div
        ref={dialog}
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="cls-title"
        aria-describedby="cls-desc"
      >
        <div className="dialog-header">
          <div className="dialog-icon warning">
            <Icon name="shield" />
          </div>
          <div>
            <h2 id="cls-title">Xác nhận phân loại tài liệu</h2>
            <p id="cls-desc" className="muted small">
              Bắt buộc ở lần tải lên đầu tiên trong mỗi phiên đăng nhập.
            </p>
          </div>
        </div>
        <div className="dialog-body">
          <div className="file-chip">
            <Icon name="file" small />
            <span>
              Bạn sắp tải lên {filenames.length} file: {filenames.join(", ")}
            </span>
          </div>
          <ul className="class-list" aria-label="Loại tài liệu được phép">
            <li className="class-ok">
              <Icon name="check" small />
              Công khai — được tải
            </li>
            <li className="class-ok">
              <Icon name="check" small />
              Nội bộ — được tải
            </li>
            <li className="class-no">
              <Icon name="x-circle" small />
              Mật — không được tải
            </li>
            <li className="class-no">
              <Icon name="x-circle" small />
              Tuyệt mật — không được tải
            </li>
          </ul>
          <label className="checkbox">
            <input ref={checkbox} type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} />
            <span>
              Tôi xác nhận các tài liệu này thuộc loại <strong>Công khai</strong> hoặc <strong>Nội bộ</strong>, không
              phải Mật hay Tuyệt mật.
            </span>
          </label>
          <p className="field-hint">
            Lượt xác nhận được ghi vào nhật ký truy cập. Nếu tải nhầm, hãy báo Trưởng nhóm BD để quản trị viên gỡ tài
            liệu.
          </p>
        </div>
        <div className="dialog-footer">
          <button className="btn btn-secondary" type="button" onClick={onCancel}>
            Hủy
          </button>
          <button className="btn btn-primary" type="button" disabled={!checked || busy} onClick={confirm}>
            Xác nhận và tải lên
          </button>
        </div>
      </div>
    </div>
  );
}
