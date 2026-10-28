import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { vi } from "vitest";
import { MeContext } from "../auth/useMe";
import type { Me } from "../api/types";
import { ToastProvider } from "../components/Toasts";

export function jsonResponse(body: unknown, status = 200): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type Handler = (init: RequestInit | undefined, url: string) => Response | Promise<Response>;

/** Mock `fetch`: khóa là "METHOD /đường-dẫn" (không gồm /api/v1, không gồm query). */
export function mockFetch(routes: Record<string, Handler>) {
  const fn = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const path = url.replace(/^\/api\/v1/, "").split("?")[0];
    const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
    const handler = routes[key];
    if (!handler) return jsonResponse({ code: "NOT_FOUND", message: key }, 404);
    return handler(init, url);
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

export function testQueryClient(): QueryClient {
  return new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
}

export function LocationProbe() {
  const loc = useLocation();
  return <div data-testid="location">{loc.pathname + loc.search}</div>;
}

export const LAN: Me = {
  user_id: "u-lan",
  email: "lan@demo.local",
  display_name: "Nguyễn Thị Lan",
  is_admin: false,
  doc_sets: [{ id: "ds-1", name: "Dự án X", role: "member" }],
};

export const MINH: Me = { ...LAN, user_id: "u-minh", email: "minh@demo.local", display_name: "Trần Văn Minh", doc_sets: [{ id: "ds-1", name: "Dự án X", role: "manager" }] };

export const HUNG: Me = { user_id: "u-hung", email: "hung@demo.local", display_name: "Phạm Văn Hùng", is_admin: true, doc_sets: [] };

/** Render một component cần router + react-query (+ người dùng hiện tại nếu truyền `me`). */
/** `path`: route gắn `ui` (mặc định "/"); điều hướng sang đường khác thì `ui` không còn hiển thị. */
export function renderWithProviders(
  ui: ReactElement,
  opts: { route?: string; path?: string; me?: Me; client?: QueryClient } = {},
) {
  const client = opts.client ?? testQueryClient();
  const content = opts.me ? <MeContext.Provider value={opts.me}>{ui}</MeContext.Provider> : ui;
  const route = opts.route ?? "/";
  const result = render(
    <QueryClientProvider client={client}>
      <ToastProvider>
        <MemoryRouter initialEntries={[route]}>
          <Routes>
            <Route path={opts.path ?? route.split("?")[0]} element={content} />
            <Route path="*" element={null} />
          </Routes>
          <LocationProbe />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  return { ...result, client };
}
