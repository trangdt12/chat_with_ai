// Sinh PDF cho bộ đánh giá (T-15) từ eval/corpus_src.json bằng Chromium của Playwright.
// Chromium dùng font hệ thống nên giữ đúng tiếng Việt có dấu; mỗi phần tử `pages` là đúng một trang PDF.
// Chạy: cd web && npx playwright install chromium && npm run eval:corpus
import { mkdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const root = fileURLToPath(new URL("../../eval/", import.meta.url));
const src = JSON.parse(await readFile(`${root}corpus_src.json`, "utf8"));
await mkdir(`${root}corpus`, { recursive: true });

const escape = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function html(doc) {
  const pages = doc.pages
    .map(
      (text, i) => `<section>
        ${i === 0 ? `<h1>${escape(doc.title)}</h1>` : ""}
        ${text.split("\n\n").map((p) => `<p>${escape(p).replace(/\n/g, "<br>")}</p>`).join("")}
        <footer>${escape(doc.file)} · Trang ${i + 1}/${doc.pages.length}</footer>
      </section>`,
    )
    .join("");
  return `<!doctype html><html lang="vi"><head><meta charset="utf-8"><style>
    @page { size: A4; margin: 20mm; }
    body { font-family: "Segoe UI", Arial, "Noto Sans", sans-serif; font-size: 12pt; line-height: 1.5; }
    section { page-break-after: always; break-after: page; position: relative; min-height: 240mm; }
    section:last-child { page-break-after: auto; break-after: auto; }
    h1 { font-size: 15pt; }
    footer { position: absolute; bottom: 0; font-size: 9pt; color: #555; }
  </style></head><body>${pages}</body></html>`;
}

const browser = await chromium.launch();
const page = await browser.newPage();
for (const doc of src.documents) {
  await page.setContent(html(doc), { waitUntil: "load" });
  await page.pdf({ path: `${root}corpus/${doc.file}`, format: "A4", printBackground: false });
  console.log(`✓ eval/corpus/${doc.file} (${doc.pages.length} trang)`);
}
await browser.close();
