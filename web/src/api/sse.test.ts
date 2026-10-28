import { describe, expect, it } from "vitest";
import { createSseParser } from "./sse";
import type { AnswerEvent } from "./types";

function parseChunks(chunks: string[]): AnswerEvent[] {
  const events: AnswerEvent[] = [];
  const parser = createSseParser((e) => events.push(e));
  chunks.forEach((c) => parser.feed(c));
  parser.flush();
  return events;
}

describe("createSseParser", () => {
  const full =
    'event: answer.started\r\ndata: {"message_id":"m1","turn_index":0}\r\n\r\n' +
    ": ping - keep-alive\r\n\r\n" +
    'event: answer.delta\r\ndata: {"text":"Thời hạn 30 ngày","citations":[]}\r\n\r\n' +
    'event: answer.completed\r\ndata: {"message_id":"m1","answer_type":"answered","citations":[],"pending_documents":[]}\r\n\r\n';

  it("parse đúng thứ tự, bỏ dòng keep-alive", () => {
    expect(parseChunks([full]).map((e) => e.event)).toEqual(["answer.started", "answer.delta", "answer.completed"]);
  });

  it("chuỗi bị cắt giữa khung (kể cả giữa \\r và \\n) vẫn parse đúng", () => {
    const pieces: string[] = [];
    for (let i = 0; i < full.length; i += 7) pieces.push(full.slice(i, i + 7));
    const events = parseChunks(pieces);
    expect(events.map((e) => e.event)).toEqual(["answer.started", "answer.delta", "answer.completed"]);
    expect(events[1]).toEqual({ event: "answer.delta", data: { text: "Thời hạn 30 ngày", citations: [] } });
  });

  it("chấp nhận xuống dòng \\n", () => {
    const events = parseChunks(['event: answer.stopped\ndata: {"message_id":"m1"}\n\n']);
    expect(events).toEqual([{ event: "answer.stopped", data: { message_id: "m1" } }]);
  });
});
