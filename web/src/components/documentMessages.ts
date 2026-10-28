// Thông báo lỗi tài liệu — nguyên văn từ màn 04 (docs/design/UI_UX_design/04-tai-tai-lieu-len.html).
import type { DocumentStatus } from "../api/types";

export function documentErrorMessage(code: string | null | undefined, filename = ""): string {
  switch (code) {
    case "NOT_PDF":
      return "Chỉ hỗ trợ file PDF.";
    case "FILE_TOO_LARGE":
    case "too_many_pages":
      return "File vượt quá giới hạn 200 trang / 20 MB.";
    case "DOC_SET_FULL":
      return `Bộ tài liệu đã đạt tối đa 50 file. File “${filename}” không được tiếp nhận.`;
    case "no_text":
      return "Không trích xuất được chữ (có thể là bản scan). Bản MVP chưa hỗ trợ PDF scan.";
    case "encrypted":
      return "File được bảo vệ bằng mật khẩu. Hãy gỡ mật khẩu rồi tải lại.";
    case "corrupt":
      return "File bị hỏng hoặc không đọc được. Hãy xuất lại PDF và thử lại.";
    default:
      return "Không xử lý được file này. Hãy thử lại.";
  }
}

export function renamedMessage(original: string, saved: string): string {
  return `${original} đã tồn tại. File mới được lưu thành ${saved}.`;
}

export const BATCH_MEMBER_MESSAGE = "Tải lô chỉ dành cho Trưởng nhóm. Hãy tải từng file.";

/** Nhãn ngắn + việc cần làm cho bảng kết quả tải lô (màn 04 #manager). */
export const ERROR_ACTIONS: Record<string, { label: string; action: string }> = {
  no_text: { label: "Bản scan", action: "Xin bản PDF gốc dạng văn bản" },
  encrypted: { label: "Có mật khẩu", action: "Gỡ mật khẩu rồi tải lại" },
  corrupt: { label: "File hỏng", action: "Xuất lại PDF" },
  too_many_pages: { label: "Quá 200 trang", action: "Tách file thành các phần ≤ 200 trang" },
  NOT_PDF: { label: "Không phải PDF", action: "Chuyển file sang PDF" },
  FILE_TOO_LARGE: { label: "Quá 20 MB", action: "Giảm dung lượng xuống ≤ 20 MB" },
  DOC_SET_FULL: { label: "Đã đủ 50 file", action: "Gỡ bớt tài liệu cũ" },
};

export function statusLabel(status: DocumentStatus, progress: number): string {
  switch (status) {
    case "uploaded":
      return "Đang chờ xử lý";
    case "processing":
      return `Đang xử lý ${progress}%`;
    case "ready":
      return "Sẵn sàng";
    case "failed":
      return "Lỗi";
  }
}
