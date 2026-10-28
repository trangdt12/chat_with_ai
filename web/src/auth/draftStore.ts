// Giữ câu hỏi đang gõ khi phiên hết hạn (AC-US012-2).
// Ô nhập (T-11) đăng ký getter; khi API trả 401, App gọi saveDraft() trước khi chuyển sang /login;
// ChatPage gọi takeDraft() khi mount để đổ lại vào ô nhập.

const KEY = "cwd.draft";

let getter: (() => string) | null = null;

export function setDraftGetter(fn: (() => string) | null): void {
  getter = fn;
}

export function saveDraft(): void {
  const value = getter?.() ?? "";
  if (!value.trim()) return;
  try {
    sessionStorage.setItem(KEY, value);
  } catch {
    // sessionStorage bị chặn — bỏ qua, không làm hỏng luồng đăng nhập lại
  }
}

/** Đọc bản nháp mà không xóa (an toàn khi React StrictMode gọi hàm khởi tạo state 2 lần). */
export function peekDraft(): string {
  try {
    return sessionStorage.getItem(KEY) ?? "";
  } catch {
    return "";
  }
}

export function takeDraft(): string {
  try {
    const value = sessionStorage.getItem(KEY) ?? "";
    sessionStorage.removeItem(KEY);
    return value;
  } catch {
    return "";
  }
}
