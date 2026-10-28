// Giới hạn phía client — chỉ để phản hồi nhanh; server luôn kiểm tra lại (README §2.5).
export const UPLOAD_MAX_BYTES = 20 * 1024 * 1024;
export const DOC_SET_MAX_DOCUMENTS = 50;
export const QUESTION_MAX_CHARS = 2000;
export const QUESTION_COUNTER_FROM = 200; // hiện bộ đếm khi còn ≤ 200 ký tự
export const DOCUMENT_POLL_MS = 3000;
export const UPLOAD_RETRIES = 3;
