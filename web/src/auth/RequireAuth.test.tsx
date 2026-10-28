import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { HUNG, LAN, jsonResponse, mockFetch, renderWithProviders } from "../test/utils";
import { RequireAuth } from "./RequireAuth";

afterEach(() => vi.unstubAllGlobals());

function renderGuard(area: "chat" | "admin", route: string) {
  return renderWithProviders(
    <RequireAuth area={area}>
      <p>nội dung được bảo vệ</p>
    </RequireAuth>,
    { route },
  );
}

describe("RequireAuth", () => {
  it("chưa đăng nhập → /login?next=", async () => {
    mockFetch({ "GET /me": () => jsonResponse({ code: "UNAUTHENTICATED", message: "" }, 401) });
    renderGuard("chat", "/");
    await vi.waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/login?next=%2F"));
    expect(screen.queryByText("nội dung được bảo vệ")).not.toBeInTheDocument();
  });

  it("không thuộc nhóm nào → /no-access", async () => {
    mockFetch({ "GET /me": () => jsonResponse({ ...LAN, doc_sets: [] }) });
    renderGuard("chat", "/");
    await vi.waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/no-access"));
  });

  it("admin không thuộc nhóm vào / → /admin", async () => {
    mockFetch({ "GET /me": () => jsonResponse(HUNG) });
    renderGuard("chat", "/");
    await vi.waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/admin"));
  });

  it("thành viên vào trang quản trị → /", async () => {
    mockFetch({ "GET /me": () => jsonResponse(LAN) });
    renderGuard("admin", "/admin");
    await vi.waitFor(() => expect(screen.getByTestId("location").textContent).toBe("/"));
  });

  it("thành viên vào / thấy nội dung", async () => {
    mockFetch({ "GET /me": () => jsonResponse(LAN) });
    renderGuard("chat", "/");
    expect(await screen.findByText("nội dung được bảo vệ")).toBeInTheDocument();
  });
});
