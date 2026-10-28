import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { UPLOAD_MAX_BYTES } from "../config";
import { UploadDropzone, validateSelection } from "./UploadDropzone";

function file(name: string, size = 1000): File {
  const f = new File(["%PDF-"], name, { type: "application/pdf" });
  Object.defineProperty(f, "size", { value: size });
  return f;
}

describe("validateSelection", () => {
  it("chặn .docx", () => {
    const sel = validateSelection([file("BaoCao.docx")], { canBatch: false, existingCount: 0 });
    expect(sel.accepted).toEqual([]);
    expect(sel.rejected).toEqual([{ name: "BaoCao.docx", code: "NOT_PDF", message: "Chỉ hỗ trợ file PDF." }]);
  });

  it("chặn file > 20 MB", () => {
    const sel = validateSelection([file("big.pdf", UPLOAD_MAX_BYTES + 1)], { canBatch: false, existingCount: 0 });
    expect(sel.rejected[0].code).toBe("FILE_TOO_LARGE");
    expect(sel.rejected[0].message).toBe("File vượt quá giới hạn 200 trang / 20 MB.");
  });

  it("member chọn nhiều file → không gửi, hướng dẫn tải từng file", () => {
    const sel = validateSelection([file("a.pdf"), file("b.pdf")], { canBatch: false, existingCount: 0 });
    expect(sel.accepted).toEqual([]);
    expect(sel.blocked).toBe("Tải lô chỉ dành cho Trưởng nhóm. Hãy tải từng file.");
  });

  it("manager tải lô; vượt 50 file thì phần dư bị từ chối", () => {
    const sel = validateSelection([file("a.pdf"), file("b.pdf"), file("c.pdf")], { canBatch: true, existingCount: 48 });
    expect(sel.accepted.map((f) => f.name)).toEqual(["a.pdf", "b.pdf"]);
    expect(sel.rejected).toEqual([
      { name: "c.pdf", code: "DOC_SET_FULL", message: "Bộ tài liệu đã đạt tối đa 50 file. File “c.pdf” không được tiếp nhận." },
    ]);
  });
});

describe("UploadDropzone", () => {
  it("chọn file qua input gọi onFiles; member không có thuộc tính multiple", () => {
    const onFiles = vi.fn();
    render(<UploadDropzone canBatch={false} onFiles={onFiles} />);
    const input = screen.getByTestId("file-input") as HTMLInputElement;
    expect(input.multiple).toBe(false);
    fireEvent.change(input, { target: { files: [file("a.pdf")] } });
    expect(onFiles).toHaveBeenCalledWith([expect.objectContaining({ name: "a.pdf" })]);
  });

  it("kéo thả file", () => {
    const onFiles = vi.fn();
    render(<UploadDropzone canBatch onFiles={onFiles} />);
    fireEvent.drop(screen.getByRole("button", { name: /Tải tài liệu PDF lên/ }), {
      dataTransfer: { files: [file("a.pdf"), file("b.pdf")] },
    });
    expect(onFiles).toHaveBeenCalledWith([expect.anything(), expect.anything()]);
  });
});
