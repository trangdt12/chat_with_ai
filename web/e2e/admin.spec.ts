import { expect, test } from "@playwright/test";
import { CONTRACT } from "./fixtures/pdf";
import { USERS, ask, docRow, login, loginNewContext, resetDb, uploadOneByOne } from "./helpers";

test.describe.configure({ mode: "serial" });
test.beforeAll(() => resetDb());

test("Hùng thêm thành viên: email sai báo lỗi tại ô, email đúng thêm dòng mới", async ({ page }) => {
  await login(page, "hung");
  await expect(page.locator("main")).not.toContainText("Hỏi đáp");
  await page.getByRole("button", { name: "Thêm thành viên" }).click();
  const dialog = page.getByRole("dialog", { name: "Thêm thành viên vào nhóm truy cập" });
  await dialog.getByLabel("Email").fill("nobody@demo.local");
  await dialog.getByRole("button", { name: "Thêm" }).click();
  await expect(dialog.getByText("Không tìm thấy tài khoản này trong hệ thống. Kiểm tra lại email.")).toBeVisible();

  await dialog.getByLabel("Email").fill("tuan@demo.local");
  await dialog.getByRole("button", { name: "Thêm" }).click();
  await expect(dialog).toBeHidden();
  await expect(page.getByRole("row", { name: new RegExp(USERS.tuan) })).toBeVisible();
});

test("Anh bị gỡ → thao tác kế tiếp ra trang không có quyền", async ({ page, browser }) => {
  const anh = await loginNewContext(browser, "anh");
  await expect(anh.page).toHaveURL(/\/$/);

  await login(page, "hung");
  await page.getByRole("button", { name: `Gỡ ${USERS.anh} khỏi nhóm` }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Gỡ khỏi nhóm" }).click();
  await expect(page.getByText(new RegExp(`Đã gỡ ${USERS.anh} khỏi nhóm`))).toBeVisible();

  // Request kế tiếp của Anh (polling danh sách / tải lại) nhận 403
  await anh.page.reload();
  await expect(anh.page).toHaveURL(/\/no-access/);
  await anh.context.close();
});

test("gỡ tài liệu → biến khỏi danh sách của Lan; trích dẫn cũ báo đã gỡ; nhật ký có các thao tác", async ({
  page,
  browser,
}) => {
  const lan = await loginNewContext(browser, "lan");
  await uploadOneByOne(lan.page, [CONTRACT]);
  await ask(lan.page, "Thời hạn thanh toán là bao lâu?");
  const cite = lan.page.locator("article.msg-assistant").last().getByRole("button", { name: /^Nguồn 1:/ });
  await expect(cite).toBeVisible();

  await login(page, "hung");
  await page.getByRole("link", { name: "Gỡ tài liệu" }).click();
  await expect(page.getByText("Bạn chỉ thấy thông tin mô tả của tài liệu, không xem được nội dung.")).toBeVisible();
  await page.getByRole("button", { name: `Gỡ ${CONTRACT.name}` }).click();
  const dialog = page.getByRole("alertdialog");
  await expect(dialog.getByRole("button", { name: "Hủy" })).toBeFocused();
  await dialog.getByLabel(/Người yêu cầu gỡ/).fill(USERS.minh);
  await dialog.getByLabel(/Lý do/).fill("Tải nhầm tài liệu");
  await dialog.getByRole("checkbox").check();
  await dialog.getByRole("button", { name: /Gỡ vĩnh viễn/ }).click();
  await expect(page.getByText(new RegExp(`Đã gỡ ${CONTRACT.name.replace(".", "\\.")}`))).toBeVisible();

  // Lan: tài liệu biến khỏi danh sách ở lần làm mới kế tiếp (polling ≤ 10 s hoặc tải lại)
  await lan.page.reload();
  await expect(docRow(lan.page, CONTRACT.name)).toHaveCount(0);

  await page.getByRole("link", { name: "Nhật ký truy cập" }).click();
  await page.getByRole("button", { name: "Tra cứu" }).click();
  const table = page.locator("table");
  for (const action of ["Đăng nhập", "Xác nhận phân loại", "Tải lên", "Hỏi đáp", "Gỡ tài liệu", "Gỡ thành viên"]) {
    await expect(table.getByText(action, { exact: true }).first()).toBeVisible();
  }
  await expect(table).toContainText("Tải nhầm tài liệu");
  await expect(table).not.toContainText("Thời hạn thanh toán là bao lâu?");
  await lan.context.close();
});
