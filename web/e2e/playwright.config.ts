import { defineConfig, devices } from "@playwright/test";

// Chạy trên máy host khi `docker compose up` đang chạy với LLM_FAKE=1, EMBED_FAKE=1 (README gốc).
// Các spec dùng chung một DB nên chạy tuần tự (workers: 1); mỗi spec tự seed lại bằng `app.seed --reset`.
const reportDir = process.env.PW_REPORT_DIR ?? "../playwright-report";
const resultsDir = process.env.PW_RESULTS_DIR ?? "../test-results";

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  // Bằng chứng cho mọi TC, kể cả PASS (TEST_PLAN.md §9): trace, ảnh, video trong test-results/, báo cáo HTML.
  // Mặc định khớp .gitignore (web/test-results/, web/playwright-report/). scripts/run-tests.sh đặt
  // PW_REPORT_DIR / PW_RESULTS_DIR để mỗi lượt chạy có thư mục riêng; results.json dùng cho docs/traceability.md.
  outputDir: "../test-results",
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: reportDir }],
    ["json", { outputFile: `${resultsDir}/results.json` }],
    ["junit", { outputFile: `${resultsDir}/junit.xml` }],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    locale: "vi-VN",
    trace: "on",
    screenshot: "on",
    video: "on",
    permissions: ["clipboard-read", "clipboard-write"],
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
});
