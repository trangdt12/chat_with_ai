import { defineConfig, devices } from "@playwright/test";

// Chạy trên máy host khi `docker compose up` đang chạy với LLM_FAKE=1, EMBED_FAKE=1 (README gốc).
// Các spec dùng chung một DB nên chạy tuần tự (workers: 1); mỗi spec tự seed lại bằng `app.seed --reset`.
export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.ts",
  fullyParallel: false,
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    locale: "vi-VN",
    trace: "retain-on-failure",
    permissions: ["clipboard-read", "clipboard-write"],
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
});
