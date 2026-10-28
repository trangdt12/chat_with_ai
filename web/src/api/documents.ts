import { UPLOAD_RETRIES } from "../config";
import { API_PREFIX, ApiError, apiFetch, handleAuthError } from "./client";
import type { DocumentOut, UploadResult } from "./types";

export function listDocuments(dsid: string): Promise<DocumentOut[]> {
  return apiFetch<DocumentOut[]>(`/doc-sets/${dsid}/documents`);
}

export function confirmClassification(dsid: string): Promise<{ confirmed_at: string }> {
  return apiFetch(`/doc-sets/${dsid}/classification-confirmations`, { method: "POST" });
}

export function documentFileUrl(documentId: string, page?: number): string {
  const base = `${API_PREFIX}/documents/${documentId}/file`;
  return page ? `${base}?page=${page}#page=${page}` : base;
}

/** Lỗi mạng khi tải lên (không nhận được phản hồi HTTP) — được thử lại. */
export class NetworkError extends Error {
  constructor() {
    super("network");
    this.name = "NetworkError";
  }
}

function parseError(xhr: XMLHttpRequest): ApiError {
  let code = xhr.status === 401 ? "UNAUTHENTICATED" : xhr.status === 403 ? "FORBIDDEN" : "INTERNAL";
  let message = "";
  try {
    const body = JSON.parse(xhr.responseText);
    if (typeof body?.code === "string") code = body.code;
    if (typeof body?.message === "string") message = body.message;
  } catch {
    // body không phải JSON
  }
  return new ApiError(xhr.status, code, message);
}

/** Dùng XHR (không phải fetch) để có phần trăm tải lên qua `xhr.upload.onprogress`. */
export function uploadFiles(
  dsid: string,
  files: File[],
  onProgress?: (percent: number) => void,
): Promise<UploadResult[]> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_PREFIX}/doc-sets/${dsid}/documents`);
    xhr.withCredentials = true;
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
    };
    xhr.onerror = () => reject(new NetworkError());
    xhr.onload = () => {
      if (xhr.status === 200) {
        try {
          resolve(JSON.parse(xhr.responseText) as UploadResult[]);
        } catch {
          reject(new ApiError(xhr.status, "INTERNAL", ""));
        }
        return;
      }
      const err = parseError(xhr);
      // 403 tải lô là lỗi nghiệp vụ (hiện hướng dẫn), không phải bị thu hồi quyền.
      if (err.status === 401) handleAuthError(err);
      reject(err);
    };
    const form = new FormData();
    for (const f of files) form.append("files", f, f.name);
    xhr.send(form);
  });
}

/** Lỗi mạng: tự thử lại tối đa 3 lần (E-10). Lỗi HTTP không thử lại. */
export async function uploadWithRetry(
  dsid: string,
  files: File[],
  opts: { onProgress?: (percent: number) => void; onRetry?: (attempt: number) => void; retryDelayMs?: number } = {},
): Promise<UploadResult[]> {
  for (let attempt = 0; ; attempt++) {
    try {
      return await uploadFiles(dsid, files, opts.onProgress);
    } catch (e) {
      if (!(e instanceof NetworkError) || attempt >= UPLOAD_RETRIES) throw e;
      opts.onRetry?.(attempt + 1);
      await new Promise((r) => setTimeout(r, opts.retryDelayMs ?? 1000 * (attempt + 1)));
    }
  }
}
