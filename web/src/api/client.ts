export const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message || code);
    this.name = "ApiError";
  }
}

type AuthHandlers = {
  onUnauthenticated?: () => void;
  onForbidden?: () => void;
};

let handlers: AuthHandlers = {};

/** App đăng ký cách xử lý 401 (về trang đăng nhập) và 403 (về trang không có quyền). */
export function setAuthHandlers(h: AuthHandlers): void {
  handlers = h;
}

export type ApiOptions = {
  /** false: không gọi handler 401/403 chung (dùng cho /me, /auth/*, và nơi tự xử lý lỗi). */
  handleAuth?: boolean;
};

export async function toApiError(res: Response): Promise<ApiError> {
  let code = res.status === 401 ? "UNAUTHENTICATED" : res.status === 403 ? "FORBIDDEN" : "INTERNAL";
  let message = "";
  try {
    const body = await res.json();
    if (typeof body?.code === "string") code = body.code;
    if (typeof body?.message === "string") message = body.message;
  } catch {
    // body không phải JSON (vd. proxy trả HTML) — giữ code theo status
  }
  return new ApiError(res.status, code, message);
}

export function handleAuthError(err: ApiError): void {
  if (err.status === 401) handlers.onUnauthenticated?.();
  else if (err.status === 403 && err.code === "FORBIDDEN") handlers.onForbidden?.();
}

export async function apiFetch<T>(path: string, init: RequestInit = {}, opts: ApiOptions = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (typeof init.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(`${API_PREFIX}${path}`, { ...init, headers, credentials: "include" });
  if (!res.ok) {
    const err = await toApiError(res);
    if (opts.handleAuth !== false) handleAuthError(err);
    throw err;
  }
  if (res.status === 204) return undefined as T;
  const type = res.headers.get("content-type") ?? "";
  return (type.includes("application/json") ? await res.json() : undefined) as T;
}

export function jsonBody(body: unknown): Pick<RequestInit, "body"> {
  return { body: JSON.stringify(body) };
}
