// Ghi các fixture e2e (web/e2e/fixtures/pdf.ts, vốn chỉ sinh trong bộ nhớ) ra đĩa để agent-browser `upload` được.
// Cùng nội dung byte với Playwright, nên kỳ vọng trong docs/test/test-cases.yaml giữ nguyên.
// Chạy: cd web && npm run e2e:fixtures   (Node ≥ 23.6 để import thẳng file .ts) → data/e2e-fixtures/
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import * as fx from "../e2e/fixtures/pdf.ts";

const out = fileURLToPath(new URL("../../data/e2e-fixtures/", import.meta.url));
await mkdir(out, { recursive: true });

for (const f of [fx.CONTRACT, fx.APPENDIX, fx.QUOTE, fx.DOCX, fx.CORRUPT, fx.SCAN]) {
  await writeFile(out + f.name, f.buffer);
  console.log(`${f.name}\t${f.buffer.length} B`);
}
