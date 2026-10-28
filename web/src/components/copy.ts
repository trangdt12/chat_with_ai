import type { CitationRef, Span } from "../api/types";

/** Bỏ cú pháp markdown, giữ nội dung đọc được (US-018). */
export function stripMarkdown(md: string): string {
  return md
    .replace(/\*\*(.+?)\*\*/gs, "$1")
    .replace(/__(.+?)__/gs, "$1")
    .replace(/(^|[^\w*])\*(?!\s)(.+?)\*(?!\w)/g, "$1$2")
    .replace(/(^|\W)_(?!\s)(.+?)_(?!\w)/g, "$1$2")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$/gm, "") // dòng phân cách bảng
    .replace(/`([^`]*)`/g, "$1")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/**
 * Văn bản thuần để dán vào email:
 *   {nội dung, bỏ markdown, chỉ số dạng [1]}
 *
 *   Nguồn:
 *   [1] HopDongKhung.pdf, trang 14
 */
export function answerToPlainText(spans: Span[], citations: CitationRef[]): string {
  const body = spans
    .map((s) => {
      const marks = s.citations.map((c) => `[${c.idx}]`).join("");
      if (!marks) return s.text;
      const m = /\s*$/.exec(s.text);
      const tail = m ? m[0] : "";
      return `${s.text.slice(0, s.text.length - tail.length)} ${marks}${tail}`;
    })
    .join("");
  const unique = [...new Map(citations.map((c) => [c.idx, c])).values()].sort((a, b) => a.idx - b.idx);
  const sources = unique.map((c) =>
    c.filename ? `[${c.idx}] ${c.filename}, trang ${c.page}` : `[${c.idx}] Tài liệu đã được gỡ`,
  );
  return `${stripMarkdown(body)}\n\nNguồn:\n${sources.join("\n")}`;
}
