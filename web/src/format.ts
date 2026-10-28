const pad = (n: number) => String(n).padStart(2, "0");

/** dd/MM/yyyy HH:mm theo giờ địa phương. */
export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
}

/** Dung lượng MB, 1 chữ số thập phân, dấu phẩy thập phân: 1258291 → "1,2 MB". */
export function formatMB(bytes: number): string {
  return `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")} MB`;
}

/** yyyy-MM-dd theo giờ địa phương (giá trị cho <input type="date">). */
export function isoDate(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export const ROLE_LABELS = { member: "Thành viên", manager: "Quản lý bộ tài liệu" } as const;
