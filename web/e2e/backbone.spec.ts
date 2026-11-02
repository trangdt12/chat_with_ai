// Đường xương sống US-001 + US-009 — các TC lớp E còn thiếu trong docs/test/test-cases.yaml.
import { expect, test } from "@playwright/test";
import { CONTRACT, QUOTE } from "./fixtures/pdf";
import { ask, chooseFiles, docRow, lastAnswer, login, resetDb, setWorker, uploadOneByOne } from "./helpers";

test.describe.configure({ mode: "serial" });

test.beforeEach(() => resetDb());

test("TC-009 câu hỏi về file vừa tải trích dẫn đúng file", async ({ page }) => {
  await login(page, "lan");
  await uploadOneByOne(page, [CONTRACT, QUOTE]);

  await ask(page, "Giá gói phần mềm bản quyền trong báo giá là bao nhiêu?");
  const answer = lastAnswer(page);
  await expect(answer.getByRole("button", { name: /^Nguồn \d+: BaoGia_v3\.pdf trang 1$/ }).first()).toBeVisible();
  await expect(answer.locator(".sources")).toContainText("BaoGia_v3.pdf · trang 1");
});

test.describe("TC-014", () => {
  test.afterEach(() => setWorker(true)); // luôn bật lại worker, kể cả khi test đỏ

  test("TC-014 câu trả lời ghi chú file chưa sẵn sàng", async ({ page }) => {
    await login(page, "lan");
    await uploadOneByOne(page, [CONTRACT]);

    setWorker(false);
    await chooseFiles(page, [QUOTE]); // cùng phiên: không hỏi lại xác nhận
    await expect(docRow(page, QUOTE.name).getByText("Đã tải lên", { exact: true })).toBeVisible();

    await ask(page, "Thời hạn thanh toán là bao lâu?");
    const answer = lastAnswer(page);
    await expect(answer.locator(".sources")).toBeVisible(); // câu trả lời đã hoàn tất
    await expect(answer.locator(".pending-note")).toContainText("BaoGia_v3.pdf");
    await expect(answer.getByRole("button", { name: /BaoGia_v3\.pdf/ })).toHaveCount(0);
  });
});

test("TC-018 không hỏi lại xác nhận trong cùng phiên", async ({ page }) => {
  await login(page, "lan");
  await uploadOneByOne(page, [CONTRACT]); // lần đầu: qua hộp xác nhận

  await chooseFiles(page, [QUOTE]);
  const dialog = page.getByRole("dialog", { name: "Xác nhận phân loại tài liệu" });
  // Hộp thoại không được xuất hiện ở bất kỳ thời điểm nào trong 2 s sau khi chọn file.
  const deadline = Date.now() + 2_000;
  while (Date.now() < deadline) {
    expect(await dialog.count()).toBe(0);
    await page.waitForTimeout(100);
  }
  await expect(docRow(page, QUOTE.name)).toBeVisible();
});
