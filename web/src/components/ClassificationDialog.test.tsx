import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ClassificationDialog } from "./ClassificationDialog";

describe("ClassificationDialog", () => {
  it("nút chính bị vô hiệu tới khi tích xác nhận", async () => {
    const onConfirm = vi.fn();
    render(<ClassificationDialog filenames={["a.pdf", "b.pdf"]} onConfirm={onConfirm} onCancel={() => {}} />);
    expect(screen.getByText(/Bạn sắp tải lên 2 file: a.pdf, b.pdf/)).toBeInTheDocument();
    const go = screen.getByRole("button", { name: "Xác nhận và tải lên" });
    expect(go).toBeDisabled();
    await userEvent.click(screen.getByRole("checkbox"));
    expect(go).toBeEnabled();
    await userEvent.click(go);
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("Esc đóng hộp thoại; focus mặc định ở ô xác nhận", async () => {
    const onCancel = vi.fn();
    render(<ClassificationDialog filenames={["a.pdf"]} onConfirm={() => {}} onCancel={onCancel} />);
    expect(screen.getByRole("checkbox")).toHaveFocus();
    await userEvent.keyboard("{Escape}");
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("Tab không thoát khỏi hộp thoại", async () => {
    render(<ClassificationDialog filenames={["a.pdf"]} onConfirm={() => {}} onCancel={() => {}} />);
    await userEvent.tab(); // checkbox → Hủy (nút chính đang bị vô hiệu)
    expect(screen.getByRole("button", { name: "Hủy" })).toHaveFocus();
    await userEvent.tab(); // quay vòng về checkbox
    expect(screen.getByRole("checkbox")).toHaveFocus();
  });
});
