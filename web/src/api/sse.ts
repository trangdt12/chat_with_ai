import { API_PREFIX, handleAuthError, toApiError } from "./client";
import type { AnswerEvent } from "./types";

/**
 * Bộ tách khung SSE: nhận từng mảnh text (có thể bị cắt giữa khung), gọi onEvent cho mỗi khung đủ.
 * Bỏ dòng bắt đầu bằng ":" (keep-alive); chấp nhận cả "\r\n" lẫn "\n".
 */
export function createSseParser(onEvent: (e: AnswerEvent) => void) {
  let buffer = "";

  function dispatch(frame: string) {
    let event = "";
    const data: string[] = [];
    for (const line of frame.split("\n")) {
      if (!line || line.startsWith(":")) continue;
      const colon = line.indexOf(":");
      const key = colon === -1 ? line : line.slice(0, colon);
      let value = colon === -1 ? "" : line.slice(colon + 1);
      if (value.startsWith(" ")) value = value.slice(1);
      if (key === "event") event = value;
      else if (key === "data") data.push(value);
    }
    if (!event || !data.length) return;
    try {
      onEvent({ event, data: JSON.parse(data.join("\n")) } as AnswerEvent);
    } catch {
      // khung hỏng — bỏ qua
    }
  }

  return {
    feed(chunk: string) {
      buffer += chunk;
      // "\r" ở cuối có thể là nửa đầu của "\r\n" — giữ lại tới mảnh sau mới chuẩn hóa.
      const tail = buffer.endsWith("\r") ? "\r" : "";
      buffer = buffer.slice(0, buffer.length - tail.length).replace(/\r\n?/g, "\n");
      let sep = buffer.indexOf("\n\n");
      while (sep !== -1) {
        dispatch(buffer.slice(0, sep));
        buffer = buffer.slice(sep + 2);
        sep = buffer.indexOf("\n\n");
      }
      buffer += tail;
    },
    flush() {
      if (buffer.trim()) dispatch(buffer);
      buffer = "";
    },
  };
}

/** Gửi câu hỏi và đọc câu trả lời SSE. HTTP != 200 trước khi stream → ném ApiError(code) từ body JSON. */
export async function streamAnswer(
  conversationId: string,
  question: string,
  onEvent: (e: AnswerEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_PREFIX}/conversations/${conversationId}/messages`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ question }),
    signal,
  });
  if (!res.ok) {
    const err = await toApiError(res);
    handleAuthError(err);
    throw err;
  }
  if (!res.body) return;
  const parser = createSseParser(onEvent);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    parser.feed(decoder.decode(value, { stream: true }));
  }
  parser.feed(decoder.decode());
  parser.flush();
}
