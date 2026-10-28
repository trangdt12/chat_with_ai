import { expect, test } from "@playwright/test";
import { CONTRACT, CORRUPT, DOCX, SCAN } from "./fixtures/pdf";
import { chooseFiles, confirmClassification, docRow, login, resetDb, waitReady } from "./helpers";

test.beforeAll(() => resetDb());

test("Lan: xác nhận phân loại → tải PDF → Đang xử lý → Sẵn sàng", async ({ page }) => {
  await login(page, "lan");
  await expect(page.getByRole("heading", { name: "Tải lên tài liệu PDF đầu tiên để bắt đầu hỏi đáp" })).toBeVisible();

  await chooseFiles(page, [CONTRACT]);
  await confirmClassification(page);
  await expect(docRow(page, CONTRACT.name)).toBeVisible();
  await waitReady(page, CONTRACT.name); // polling tự cập nhật, không tải lại trang
  await expect(docRow(page, CONTRACT.name)).toContainText("3 trang");
});

test(".docx và PDF hỏng báo lỗi riêng từng file, PDF scan báo không trích xuất được chữ", async ({ page }) => {
  await login(page, "lan");
  // Lần tải đầu của phiên mới lại cần xác nhận phân loại
  await chooseFiles(page, [CORRUPT]);
  await confirmClassification(page);
  await expect(docRow(page, CORRUPT.name).getByText("File bị hỏng hoặc không đọc được", { exact: false })).toBeVisible({
    timeout: 60_000,
  });

  await chooseFiles(page, [DOCX]);
  await expect(page.getByText(`${DOCX.name}: Chỉ hỗ trợ file PDF.`)).toBeVisible();
  await expect(docRow(page, DOCX.name)).toHaveCount(0);

  await chooseFiles(page, [SCAN]);
  await expect(docRow(page, SCAN.name).getByText(/Không trích xuất được chữ/)).toBeVisible({ timeout: 60_000 });
  await expect(docRow(page, CORRUPT.name).getByText("Sẵn sàng")).toHaveCount(0);
});

test("Lan chọn 2 file → bị từ chối, hướng dẫn tải từng file", async ({ page }) => {
  await login(page, "lan");
  // Member không có thuộc tính multiple, nên thả 2 file vào vùng kéo thả
  const dropzone = page.locator("#docs-panel .dropzone");
  const dataTransfer = await page.evaluateHandle(() => {
    const dt = new DataTransfer();
    dt.items.add(new File(["%PDF-1.4"], "a.pdf", { type: "application/pdf" }));
    dt.items.add(new File(["%PDF-1.4"], "b.pdf", { type: "application/pdf" }));
    return dt;
  });
  await dropzone.dispatchEvent("drop", { dataTransfer });
  await expect(page.getByText("Tải lô chỉ dành cho Trưởng nhóm. Hãy tải từng file.")).toBeVisible();
  await expect(docRow(page, "a.pdf")).toHaveCount(0);
});
