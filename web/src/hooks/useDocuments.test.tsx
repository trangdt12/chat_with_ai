import { QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { DocumentOut } from "../api/types";
import { jsonResponse, mockFetch, testQueryClient } from "../test/utils";
import { pollInterval, useDocuments } from "./useDocuments";

const doc = (status: DocumentOut["status"], id: string = status): DocumentOut => ({
  id,
  filename: `${id}.pdf`,
  pages: 3,
  size_bytes: 10,
  status,
  progress: status === "processing" ? 40 : 0,
  error_code: null,
  uploaded_by: "Lan",
  uploaded_at: "2026-10-26T00:00:00Z",
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("pollInterval", () => {
  it("có file processing → 3 s; hết → dừng", () => {
    expect(pollInterval([doc("ready"), doc("processing")])).toBe(3000);
    expect(pollInterval([doc("uploaded")])).toBe(3000);
    expect(pollInterval([doc("ready"), doc("failed")])).toBe(false);
    expect(pollInterval(undefined)).toBe(false);
  });
});

describe("useDocuments", () => {
  it("polling tới khi tài liệu sẵn sàng rồi dừng", async () => {
    let calls = 0;
    const fetch = mockFetch({
      "GET /doc-sets/ds-1/documents": () => jsonResponse([doc(++calls < 3 ? "processing" : "ready", "a")]),
    });
    const client = testQueryClient();
    const wrapper = ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    const { result } = renderHook(() => useDocuments("ds-1"), { wrapper });
    await waitFor(() => expect(result.current.readyCount).toBe(1), { timeout: 10_000 });
    const after = fetch.mock.calls.length;
    await new Promise((r) => setTimeout(r, 3500));
    expect(fetch.mock.calls.length).toBe(after); // đã dừng polling
  }, 20_000);
});
