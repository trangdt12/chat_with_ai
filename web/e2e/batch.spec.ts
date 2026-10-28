import { expect, test } from "@playwright/test";
import { APPENDIX, CONTRACT, QUOTE } from "./fixtures/pdf";
import { chooseFiles, confirmClassification, docRow, login, resetDb, waitReady } from "./helpers";

test.beforeAll(() => resetDb());

test("Minh tải 3 file một lần → 3 dòng trạng thái riêng → đều Sẵn sàng", async ({ page }) => {
  await login(page, "minh");
  await chooseFiles(page, [CONTRACT, APPENDIX, QUOTE]);
  await confirmClassification(page);

  for (const f of [CONTRACT, APPENDIX, QUOTE]) await expect(docRow(page, f.name)).toHaveCount(1);
  const panel = page.getByRole("region", { name: /Kết quả tải lô · 3 file/ });
  await expect(panel).toBeVisible();

  for (const f of [CONTRACT, APPENDIX, QUOTE]) await waitReady(page, f.name);
  await expect(panel.locator(".stat").filter({ hasText: "Sẵn sàng" }).locator(".stat-num")).toHaveText("3");
});
