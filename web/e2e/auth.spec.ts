import { expect, test } from "@playwright/test";
import { USERS, login, resetDb } from "./helpers";

test.beforeAll(() => resetDb());

test("chưa đăng nhập mở / → về trang đăng nhập", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveURL(/\/login/);
  await expect(page.getByRole("heading", { name: "Chat với tài liệu" })).toBeVisible();
  await expect(page.getByText("Đăng nhập thử nghiệm")).toBeVisible();
});

test("chưa đăng nhập mở /admin → về trang đăng nhập", async ({ page }) => {
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/login\?next=%2Fadmin/);
});

test("Lan đăng nhập → thấy bộ tài liệu; đăng xuất thì Back không vào lại được", async ({ page }) => {
  await login(page, "lan");
  await expect(page).toHaveURL(/\/$/);
  await expect(page.locator(".topbar")).toContainText(USERS.lan);
  await expect(page.locator(".topbar")).toContainText("Dự án X");

  await page.getByRole("button", { name: "Đăng xuất" }).click();
  await expect(page).toHaveURL(/\/login/);
  await page.goBack();
  await expect(page).toHaveURL(/\/login/);
});

test("người ngoài nhóm → trang không có quyền, không lộ tên bộ tài liệu", async ({ page }) => {
  await login(page, "tuan");
  await expect(page).toHaveURL(/\/no-access/);
  await expect(page.getByRole("heading", { name: "Bạn chưa có quyền truy cập bộ tài liệu nào" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("Dự án X");
});

test("admin không thuộc nhóm → trang quản trị", async ({ page }) => {
  await login(page, "hung");
  await expect(page).toHaveURL(/\/admin/);
  await expect(page.getByRole("heading", { name: /Nhóm truy cập/ })).toBeVisible();
});
