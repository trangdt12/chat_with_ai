import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";
import { DOC_SET_MAX_DOCUMENTS, UPLOAD_MAX_BYTES } from "../config";
import { BATCH_MEMBER_MESSAGE, documentErrorMessage } from "./documentMessages";
import { Icon } from "./Icon";

export type Rejected = { name: string; code: string; message: string };
export type Selection = { accepted: File[]; rejected: Rejected[]; blocked: string | null };

/** Kiểm tra phía client (đuôi .pdf, ≤ 20 MB, tổng ≤ 50 file, member chỉ 1 file). Server luôn kiểm tra lại. */
export function validateSelection(files: File[], opts: { canBatch: boolean; existingCount: number }): Selection {
  if (files.length > 1 && !opts.canBatch) {
    return { accepted: [], rejected: [], blocked: BATCH_MEMBER_MESSAGE };
  }
  const accepted: File[] = [];
  const rejected: Rejected[] = [];
  for (const f of files) {
    if (!f.name.toLowerCase().endsWith(".pdf")) {
      rejected.push({ name: f.name, code: "NOT_PDF", message: documentErrorMessage("NOT_PDF") });
    } else if (f.size > UPLOAD_MAX_BYTES) {
      rejected.push({ name: f.name, code: "FILE_TOO_LARGE", message: documentErrorMessage("FILE_TOO_LARGE") });
    } else if (opts.existingCount + accepted.length >= DOC_SET_MAX_DOCUMENTS) {
      rejected.push({ name: f.name, code: "DOC_SET_FULL", message: documentErrorMessage("DOC_SET_FULL", f.name) });
    } else {
      accepted.push(f);
    }
  }
  return { accepted, rejected, blocked: null };
}

type Props = {
  canBatch: boolean;
  onFiles: (files: File[]) => void;
  disabled?: boolean;
  large?: boolean;
};

export function UploadDropzone({ canBatch, onFiles, disabled, large }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [active, setActive] = useState(false);

  function pick() {
    if (!disabled) input.current?.click();
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setActive(false);
    if (!disabled && e.dataTransfer.files.length) onFiles(Array.from(e.dataTransfer.files));
  }

  function onKey(e: KeyboardEvent) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      pick();
    }
  }

  return (
    <div
      className={`dropzone${large ? " dropzone-lg" : ""}${active ? " is-active" : ""}`}
      style={large ? { width: "100%", margin: 0 } : undefined}
      role="button"
      tabIndex={0}
      aria-disabled={disabled || undefined}
      aria-label="Tải tài liệu PDF lên: kéo thả hoặc bấm để chọn file"
      onClick={pick}
      onKeyDown={onKey}
      onDragOver={(e) => {
        e.preventDefault();
        setActive(true);
      }}
      onDragLeave={() => setActive(false)}
      onDrop={onDrop}
    >
      <Icon name="upload" />
      <span>
        <strong>{active ? "Thả file để tải lên" : "Kéo thả PDF vào đây"}</strong> hoặc <u>chọn file</u>
      </span>
      <span className="small">
        {canBatch
          ? "Tải lô tối đa 50 file · mỗi file ≤ 200 trang, 20 MB"
          : "Mỗi lần một file · tối đa 200 trang, 20 MB"}
      </span>
      <input
        ref={input}
        type="file"
        accept=".pdf,application/pdf"
        multiple={canBatch}
        hidden
        data-testid="file-input"
        onChange={(e) => {
          const files = Array.from(e.target.files ?? []);
          e.target.value = "";
          if (files.length) onFiles(files);
        }}
      />
    </div>
  );
}
