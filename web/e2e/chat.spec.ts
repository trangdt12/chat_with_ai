import { expect, test } from "@playwright/test";
import { CONTRACT } from "./fixtures/pdf";
import { ask, lastAnswer, login, resetDb, uploadOneByOne } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeAll(async ({ browser }) => {
  resetDb();
  const page = await browser.newPage();
  await login(page, "lan");
  await uploadOneByOne(page, [CONTRACT]);
  await page.close();
});

test.beforeEach(async ({ page }) => {
  await login(page, "lan");
});

test("hỏi → stream → [1] → popover → mở PDF đúng trang", async ({ page, context }) => {
  await ask(page, "Thời hạn thanh toán là bao lâu?");
  const answer = lastAnswer(page);
  const cite = answer.getByRole("button", { name: /^Nguồn 1: HopDongKhung\.pdf trang \d+$/ });
  await expect(cite).toBeVisible();
  await expect(answer.locator(".sources")).toContainText("HopDongKhung.pdf · trang");

  await cite.click();
  const popover = page.getByRole("dialog");
  await expect(popover.locator(".popover-quote")).toContainText("thanh toan");
  // Chromium headless thường biến PDF thành tải xuống nên không đọc được URL của tab mới:
  // bắt URL truyền cho window.open, rồi tự gọi URL đó.
  await page.evaluate(() => {
    const opened: string[] = [];
    (window as unknown as { __opened: string[] }).__opened = opened;
    window.open = (url?: string | URL) => {
      opened.push(String(url));
      return null;
    };
  });
  await popover.getByRole("button", { name: /Mở tài liệu gốc tại trang \d+/ }).click();
  const url = await page.evaluate(() => (window as unknown as { __opened: string[] }).__opened[0]);
  expect(url).toMatch(/\/api\/v1\/documents\/.+\/file\?page=\d+#page=\d+$/);
  const res = await context.request.get(new URL(url.split("#")[0], page.url()).toString());
  expect(res.status()).toBe(200);
  expect(res.headers()["content-type"]).toContain("application/pdf");
});

test("bàn phím: Tab tới [1], Enter mở, Esc đóng và trả focus", async ({ page }) => {
  await ask(page, "Thời hạn thanh toán là bao lâu?");
  const cite = lastAnswer(page).getByRole("button", { name: /^Nguồn 1:/ });
  await expect(cite).toBeVisible();
  await cite.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(cite).toBeFocused();
});

test("câu hỏi tiếp nối, câu không có trong tài liệu, Hội thoại mới", async ({ page }) => {
  await ask(page, "Thời hạn thanh toán là bao lâu?");
  await expect(lastAnswer(page).locator(".sources")).toBeVisible();
  await ask(page, "Điều khoản đó có ngoại lệ khi chậm giao hàng không?");
  await expect(page.locator("article.msg-assistant")).toHaveCount(2);
  await expect(lastAnswer(page).locator(".sources")).toBeVisible();

  await ask(page, "Thủ đô của Pháp là gì?");
  await expect(lastAnswer(page)).toContainText("Không tìm thấy thông tin này trong các tài liệu đã tải lên.");

  await page.getByRole("button", { name: "Hội thoại mới" }).click();
  await expect(page.locator("article.msg-assistant")).toHaveCount(0);
  await expect(page.locator("#docs-panel .doc-row")).toHaveCount(1);
});

test("Dừng giữa chừng → nhãn đã dừng, ô nhập dùng được", async ({ page }) => {
  await ask(page, "Tóm tắt thời hạn thanh toán là bao nhiêu ngày");
  const stop = page.getByRole("button", { name: "Dừng" });
  await expect(stop).toBeVisible();
  await expect(lastAnswer(page).locator(".answer-body")).toBeVisible();
  await stop.click();
  await expect(lastAnswer(page)).toContainText("Đã dừng theo yêu cầu của bạn");
  await expect(page.getByRole("button", { name: "Gửi" })).toBeVisible();
  await expect(page.getByLabel("Câu hỏi về tài liệu")).toBeEnabled();
});

test("Sao chép kèm nguồn", async ({ page }) => {
  await ask(page, "Thời hạn thanh toán là bao lâu?");
  await lastAnswer(page).getByRole("button", { name: /Sao chép kèm nguồn/ }).click();
  await expect(page.getByText(/Đã sao chép câu trả lời kèm nguồn/)).toBeVisible();
  const text = await page.evaluate(() => navigator.clipboard.readText());
  expect(text).toMatch(/\[1\]/);
  expect(text).toMatch(/Nguồn:\n\[1\] HopDongKhung\.pdf, trang \d+/);
});

test("👎 kèm lý do", async ({ page }) => {
  await ask(page, "Thời hạn thanh toán là bao lâu?");
  const answer = lastAnswer(page);
  await answer.getByRole("button", { name: "Câu trả lời chưa tốt" }).click();
  await answer.getByLabel("Thiếu thông tin").check();
  await answer.getByRole("button", { name: "Gửi đánh giá" }).click();
  await expect(answer.getByRole("button", { name: "Câu trả lời chưa tốt" })).toHaveAttribute("aria-pressed", "true");
});

test("ô nhập rỗng: Enter không gửi", async ({ page }) => {
  const box = page.getByLabel("Câu hỏi về tài liệu");
  await box.fill("   ");
  await box.press("Enter");
  await expect(page.locator("article.msg-assistant")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Gửi" })).toBeDisabled();
});
