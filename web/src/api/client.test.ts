import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse, mockFetch } from "../test/utils";
import { ApiError, apiFetch, setAuthHandlers } from "./client";

afterEach(() => {
  setAuthHandlers({});
  vi.unstubAllGlobals();
});

describe("apiFetch", () => {
  it("thêm /api/v1, gửi cookie và trả JSON", async () => {
    const fetch = mockFetch({ "GET /me": () => jsonResponse({ email: "lan@demo.local" }) });
    await expect(apiFetch("/me")).resolves.toEqual({ email: "lan@demo.local" });
    expect(fetch).toHaveBeenCalledWith("/api/v1/me", expect.objectContaining({ credentials: "include" }));
  });

  it("401 gọi onUnauthenticated và ném ApiError", async () => {
    const onUnauthenticated = vi.fn();
    setAuthHandlers({ onUnauthenticated });
    mockFetch({ "GET /me": () => jsonResponse({ code: "UNAUTHENTICATED", message: "" }, 401) });
    await expect(apiFetch("/me")).rejects.toMatchObject({ status: 401, code: "UNAUTHENTICATED" });
    expect(onUnauthenticated).toHaveBeenCalledOnce();
  });

  it("handleAuth=false không gọi handler", async () => {
    const onUnauthenticated = vi.fn();
    setAuthHandlers({ onUnauthenticated });
    mockFetch({ "GET /me": () => jsonResponse({ code: "UNAUTHENTICATED", message: "" }, 401) });
    await expect(apiFetch("/me", {}, { handleAuth: false })).rejects.toBeInstanceOf(ApiError);
    expect(onUnauthenticated).not.toHaveBeenCalled();
  });

  it("403 FORBIDDEN gọi onForbidden", async () => {
    const onForbidden = vi.fn();
    setAuthHandlers({ onForbidden });
    mockFetch({ "GET /x": () => jsonResponse({ code: "FORBIDDEN", message: "" }, 403) });
    await expect(apiFetch("/x")).rejects.toMatchObject({ code: "FORBIDDEN" });
    expect(onForbidden).toHaveBeenCalledOnce();
  });

  it("lỗi JSON → ApiError mang đúng code", async () => {
    mockFetch({ "POST /x": () => jsonResponse({ code: "DOC_SET_FULL", message: "Đầy" }, 409) });
    const err = (await apiFetch("/x", { method: "POST", body: "{}" }).catch((e) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("DOC_SET_FULL");
    expect(err.message).toBe("Đầy");
  });

  it("204 trả undefined", async () => {
    mockFetch({ "POST /auth/logout": () => new Response(null, { status: 204 }) });
    await expect(apiFetch("/auth/logout", { method: "POST" })).resolves.toBeUndefined();
  });
});
