import { useQueryClient } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { ApiError } from "../api/client";
import { NetworkError, confirmClassification, uploadWithRetry } from "../api/documents";
import type { UploadResult } from "../api/types";
import type { BatchRun } from "../components/BatchResultPanel";
import { ClassificationDialog } from "../components/ClassificationDialog";
import { BATCH_MEMBER_MESSAGE, documentErrorMessage, renamedMessage } from "../components/documentMessages";
import { useToast } from "../components/Toasts";
import { validateSelection, type Rejected } from "../components/UploadDropzone";
import { documentsKey } from "./useDocuments";

export type UploadingFile = { name: string; percent: number; retry: number };

/**
 * Luồng tải lên (T-07 §2.2): kiểm tra phía client → gửi → 409 CLASSIFICATION_REQUIRED thì mở hộp xác nhận,
 * xác nhận xong gửi lại đúng các file đó → báo kết quả riêng từng file.
 */
export function useUpload(dsid: string, opts: { canBatch: boolean; existingCount: number }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [uploading, setUploading] = useState<UploadingFile[]>([]);
  const [pending, setPending] = useState<{ files: File[]; rejected: Rejected[] } | null>(null);
  const [batch, setBatch] = useState<BatchRun | null>(null);

  function report(files: File[], results: UploadResult[]) {
    results.forEach((r, i) => {
      const sent = files[i]?.name ?? r.filename;
      if (r.error_code) toast(`${sent}: ${documentErrorMessage(r.error_code, sent)}`, "danger");
      else if (r.filename !== sent) toast(renamedMessage(sent, r.filename));
    });
  }

  async function send(files: File[], rejected: Rejected[]) {
    setUploading(files.map((f) => ({ name: f.name, percent: 0, retry: 0 })));
    try {
      const results = await uploadWithRetry(dsid, files, {
        onProgress: (percent) => setUploading((xs) => xs.map((x) => ({ ...x, percent }))),
        onRetry: (retry) => setUploading((xs) => xs.map((x) => ({ ...x, retry }))),
      });
      report(files, results);
      if (opts.canBatch && files.length + rejected.length > 1) {
        setBatch({ startedAt: new Date(), results, rejected: rejected.map((r) => ({ name: r.name, code: r.code })) });
      }
    } catch (e) {
      if (e instanceof ApiError && e.code === "CLASSIFICATION_REQUIRED") {
        setPending({ files, rejected });
      } else if (e instanceof ApiError && e.status === 403) {
        toast(e.message || BATCH_MEMBER_MESSAGE, "danger");
      } else if (e instanceof NetworkError) {
        toast("Mất kết nối. Không tải được file, hãy thử lại.", "danger");
      } else if (!(e instanceof ApiError && e.status === 401)) {
        toast(e instanceof ApiError && e.message ? e.message : "Không tải được file. Hãy thử lại.", "danger");
      }
    } finally {
      setUploading([]);
      qc.invalidateQueries({ queryKey: documentsKey(dsid) });
    }
  }

  function start(files: File[]) {
    const sel = validateSelection(files, opts);
    if (sel.blocked) {
      toast(sel.blocked, "danger");
      return;
    }
    for (const r of sel.rejected) toast(`${r.name}: ${r.message}`, "danger");
    if (sel.accepted.length) void send(sel.accepted, sel.rejected);
  }

  let dialog: ReactNode = null;
  if (pending) {
    dialog = (
      <ClassificationDialog
        filenames={pending.files.map((f) => f.name)}
        onCancel={() => setPending(null)}
        onConfirm={async () => {
          try {
            await confirmClassification(dsid);
          } catch {
            toast("Không ghi nhận được xác nhận. Hãy thử lại.", "danger");
            return;
          }
          const { files, rejected } = pending;
          setPending(null);
          void send(files, rejected);
        }}
      />
    );
  }

  return { start, uploading, dialog, batch, closeBatch: () => setBatch(null), busy: uploading.length > 0 };
}
