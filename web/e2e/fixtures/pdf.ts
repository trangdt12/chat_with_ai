// Sinh file mẫu cho e2e trong bộ nhớ (thay cho file nhị phân trong repo).
// PDF dùng font Helvetica chuẩn nên chỉ có chữ Latin không dấu; FakeEmbedder và tìm kiếm từ khóa đều bỏ dấu,
// nên câu hỏi tiếng Việt có dấu vẫn khớp nội dung.

export type FilePayload = { name: string; mimeType: string; buffer: Buffer };

function escapePdf(s: string): string {
  return s.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
}

function wrap(text: string, width = 90): string[] {
  const lines: string[] = [];
  for (const para of text.split("\n")) {
    let line = "";
    for (const word of para.split(/\s+/).filter(Boolean)) {
      if ((line + " " + word).trim().length > width) {
        lines.push(line);
        line = word;
      } else {
        line = (line + " " + word).trim();
      }
    }
    lines.push(line);
  }
  return lines;
}

export function makePdf(pages: string[]): Buffer {
  const objects: string[] = [];
  const pageIds = pages.map((_, i) => 4 + 2 * i);
  objects.push("<< /Type /Catalog /Pages 2 0 R >>");
  objects.push(`<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pages.length} >>`);
  objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>");
  pages.forEach((text, i) => {
    objects.push(
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R >> >> /Contents ${pageIds[i] + 1} 0 R >>`,
    );
    const ops = text ? ["BT", "/F1 11 Tf", "14 TL", "50 800 Td", ...wrap(text).map((l) => `(${escapePdf(l)}) Tj T*`), "ET"] : [];
    const stream = ops.join("\n");
    objects.push(`<< /Length ${Buffer.byteLength(stream, "latin1")} >>\nstream\n${stream}\nendstream`);
  });

  let out = "%PDF-1.4\n";
  const offsets: number[] = [];
  objects.forEach((body, i) => {
    offsets.push(Buffer.byteLength(out, "latin1"));
    out += `${i + 1} 0 obj\n${body}\nendobj\n`;
  });
  const xref = Buffer.byteLength(out, "latin1");
  out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (const off of offsets) out += `${String(off).padStart(10, "0")} 00000 n \n`;
  out += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(out, "latin1");
}

const pdf = (name: string, pages: string[]): FilePayload => ({ name, mimeType: "application/pdf", buffer: makePdf(pages) });

export const CONTRACT = pdf("HopDongKhung.pdf", [
  "Hop dong khung so HD-2024-017 giua Cong ty A va Cong ty B.",
  "Thoi han thanh toan la 30 ngay ke tu ngay nhan hoa don hop le.",
  "Ngoai le: khi cham giao hang, thoi han thanh toan duoc gia han them 15 ngay.",
]);

export const APPENDIX = pdf("PhuLuc2.pdf", [
  "Phu luc 2 cua hop dong khung. Don hang tren 1 ty dong co thoi han thanh toan 45 ngay.",
]);

export const QUOTE = pdf("BaoGia_v3.pdf", [
  "Bao gia v3. Goi phan mem ban quyen 450 trieu dong. Trien khai va dao tao 120 trieu dong.",
]);

export const DOCX: FilePayload = {
  name: "BaoCao.docx",
  mimeType: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  buffer: Buffer.concat([Buffer.from("PK\x03\x04", "latin1"), Buffer.alloc(64)]),
};

export const CORRUPT: FilePayload = {
  name: "BangGia_cu.pdf",
  mimeType: "application/pdf",
  buffer: Buffer.from("%PDF-1.4\n1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\nkhong phai pdf\n%%EOF\n", "latin1"),
};

export const SCAN = pdf("scan_bienban.pdf", ["", "", "", "", ""]);
