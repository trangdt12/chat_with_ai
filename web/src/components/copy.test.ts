import { describe, expect, it } from "vitest";
import type { CitationRef } from "../api/types";
import { answerToPlainText } from "./copy";

const c1: CitationRef = { idx: 1, citation_id: "c1", document_id: "d1", filename: "HopDongKhung.pdf", page: 14 };
const c2: CitationRef = { idx: 2, citation_id: "c2", document_id: "d2", filename: "PhuLuc2.pdf", page: 3 };

describe("answerToPlainText", () => {
  it("bỏ markdown, chỉ số dạng [n], danh sách nguồn văn bản thuần", () => {
    const text = answerToPlainText(
      [
        { text: "Thời hạn thanh toán là **30 ngày**.", citations: [c1] },
        { text: "\n\n- Phụ lục: *45 ngày* cho đơn trên 1 tỷ.", citations: [c2] },
      ],
      [c1, c2],
    );
    expect(text).toBe(
      "Thời hạn thanh toán là 30 ngày. [1]\n\n- Phụ lục: 45 ngày cho đơn trên 1 tỷ. [2]\n\n" +
        "Nguồn:\n[1] HopDongKhung.pdf, trang 14\n[2] PhuLuc2.pdf, trang 3",
    );
  });

  it("trích dẫn đã gỡ", () => {
    const removed = { ...c1, filename: null, document_id: null };
    expect(answerToPlainText([{ text: "A", citations: [removed] }], [removed])).toBe(
      "A [1]\n\nNguồn:\n[1] Tài liệu đã được gỡ",
    );
  });
});
