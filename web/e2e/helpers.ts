import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, type Browser, type Page } from "@playwright/test";
import type { FilePayload } from "./fixtures/pdf";

const REPO_ROOT = fileURLToPath(new URL("../..", import.meta.url));

/** Đặt lại dữ liệu mẫu (xóa DB + file đã tải). Đổi lệnh qua E2E_RESET_CMD nếu không chạy bằng docker compose. */
export function resetDb(): void {
  const cmd = process.env.E2E_RESET_CMD ?? "docker compose exec -T api python -m app.seed --reset";
  execSync(cmd, { cwd: REPO_ROOT, stdio: "inherit" });
}

export const USERS = {
  lan: "Nguyễn Thị Lan",
  minh: "Trần Văn Minh",
  hung: "Phạm Văn Hùng",
  tuan: "Lê Minh Tuấn",
  anh: "Phạm Đức Anh",
} as const;

export async function login(page: Page, who: keyof typeof USERS, path = "/"): Promise<void> {
  await page.goto(path);
  await page.getByRole("button", { name: new RegExp(USERS[who]) }).click();
}

export async function loginNewContext(browser: Browser, who: keyof typeof USERS) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await login(page, who);
  return { context, page };
}

/** Chọn file qua ô input ẩn của vùng kéo thả (thanh tài liệu). */
export async function chooseFiles(page: Page, files: FilePayload[]): Promise<void> {
  await page.locator("#docs-panel [data-testid=file-input]").setInputFiles(files);
}

/** Lần tải đầu trong phiên: tích xác nhận phân loại rồi tải lên. */
export async function confirmClassification(page: Page): Promise<void> {
  const dialog = page.getByRole("dialog", { name: "Xác nhận phân loại tài liệu" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Xác nhận và tải lên" })).toBeDisabled();
  await dialog.getByRole("checkbox").check();
  await dialog.getByRole("button", { name: "Xác nhận và tải lên" }).click();
  await expect(dialog).toBeHidden();
}

export function docRow(page: Page, filename: string) {
  return page.locator("#docs-panel .doc-row").filter({ hasText: filename });
}

export async function waitReady(page: Page, filename: string): Promise<void> {
  await expect(docRow(page, filename).getByText("Sẵn sàng", { exact: true })).toBeVisible({ timeout: 60_000 });
}

/** Lan đăng nhập, tải tài liệu (qua hộp xác nhận) và chờ tất cả "Sẵn sàng". */
export async function uploadOneByOne(page: Page, files: FilePayload[]): Promise<void> {
  let first = true;
  for (const f of files) {
    await chooseFiles(page, [f]);
    if (first) await confirmClassification(page);
    first = false;
    await waitReady(page, f.name);
  }
}

export async function ask(page: Page, question: string): Promise<void> {
  const box = page.getByLabel("Câu hỏi về tài liệu");
  await box.fill(question);
  await box.press("Enter");
}

export function lastAnswer(page: Page) {
  return page.locator("article.msg-assistant").last();
}
