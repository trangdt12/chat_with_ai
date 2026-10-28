import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AdminDocument, AuditItem } from "../../api/types";
import { HUNG, jsonResponse, mockFetch, renderWithProviders } from "../../test/utils";
import { AddMemberDialog } from "./AddMemberDialog";
import { auditNote } from "./AuditTab";
import { PurgeDialog } from "./PurgeDialog";

afterEach(() => vi.unstubAllGlobals());

const item = (action: string, meta: Record<string, unknown>): AuditItem => ({
  id: 1,
  ts: "2026-10-26T03:00:00Z",
  user_id: "u",
  user_email: "hung@demo.local",
  action,
  document_id: null,
  document_filename: null,
  meta,
});

describe("auditNote", () => {
  const people = new Map([["u-lan", "lan@demo.local"]]);
  it("dựng ghi chú từ meta, không có nội dung", () => {
    expect(auditNote(item("remove_document", { requested_by: "Minh", reason: "Tải nhầm", pages: 6 }), people)).toBe(
      "Yêu cầu: Minh · “Tải nhầm” · 6 trang",
    );
    expect(auditNote(item("query", { citation_count: 3, answer_type: "answered", status: "completed" }), people)).toBe(
      "3 nguồn trích dẫn · đã trả lời",
    );
    expect(auditNote(item("role_change", { target_user_id: "u-lan", from: "member", to: "manager" }), people)).toBe(
      "lan@demo.local · Thành viên → Quản lý bộ tài liệu",
    );
    expect(auditNote(item("view_citation", {}), people)).toBe("");
  });
});

describe("PurgeDialog", () => {
  const doc: AdminDocument = {
    id: "d1",
    filename: "BienBanHop.pdf",
    pages: 6,
    size_bytes: 1_258_291,
    status: "ready",
    error_code: null,
    uploaded_by_email: "lan@demo.local",
    uploaded_at: "2026-10-26T03:24:00Z",
  };

  it("focus ở Hủy; nút Gỡ vĩnh viễn chỉ bật khi đủ 2 ô và đã tích", async () => {
    const fetch = mockFetch({ "DELETE /admin/documents/d1": () => jsonResponse({ id: "d1", removed: true }) });
    const onPurged = vi.fn();
    renderWithProviders(<PurgeDialog doc={doc} onClose={vi.fn()} onPurged={onPurged} />, { me: HUNG });
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hủy" })).toHaveFocus();
    const go = screen.getByRole("button", { name: /Gỡ vĩnh viễn/ });
    expect(go).toBeDisabled();
    await userEvent.type(screen.getByLabelText(/Người yêu cầu gỡ/), "Trần Văn Minh");
    await userEvent.type(screen.getByLabelText(/Lý do/), "Tải nhầm");
    expect(go).toBeDisabled();
    await userEvent.click(screen.getByRole("checkbox"));
    expect(go).toBeEnabled();
    await userEvent.click(go);
    await vi.waitFor(() => expect(onPurged).toHaveBeenCalled());
    expect(JSON.parse(fetch.mock.calls[0][1]!.body as string)).toEqual({
      requested_by: "Trần Văn Minh",
      reason: "Tải nhầm",
    });
  });
});

describe("AddMemberDialog", () => {
  it("USER_NOT_FOUND hiện lỗi ngay dưới ô email", async () => {
    mockFetch({
      "POST /admin/doc-sets/ds-1/members": () => jsonResponse({ code: "USER_NOT_FOUND", message: "" }, 404),
    });
    renderWithProviders(<AddMemberDialog docSetId="ds-1" onClose={vi.fn()} onAdded={vi.fn()} />, { me: HUNG });
    await userEvent.type(screen.getByLabelText("Email"), "nobody@demo.local");
    await userEvent.click(screen.getByRole("button", { name: "Thêm" }));
    expect(
      await screen.findByText("Không tìm thấy tài khoản này trong hệ thống. Kiểm tra lại email."),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveAttribute("aria-invalid", "true");
  });
});
