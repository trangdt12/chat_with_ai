import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../api/client";
import { createConversation, stopMessage } from "../api/qa";
import { streamAnswer } from "../api/sse";
import type { AnswerEvent, CitationRef, Turn } from "../api/types";

let nextKey = 1;

function newTurn(question: string): Turn {
  return {
    key: `t${nextKey++}`,
    question,
    messageId: null,
    spans: [],
    status: "streaming",
    answerType: null,
    citations: [],
    pendingDocuments: [],
    failCode: null,
    feedback: null,
  };
}

function mergeCitations(existing: CitationRef[], incoming: CitationRef[]): CitationRef[] {
  const byIdx = new Map(existing.map((c) => [c.idx, c]));
  for (const c of incoming) if (!byIdx.has(c.idx)) byIdx.set(c.idx, c);
  return [...byIdx.values()].sort((a, b) => a.idx - b.idx);
}

/** Áp một sự kiện SSE vào lượt hỏi đáp. Lượt đã dừng phía UI thì bỏ qua delta đến sau. */
export function applyEvent(turn: Turn, ev: AnswerEvent): Turn {
  switch (ev.event) {
    case "answer.started":
      return { ...turn, messageId: ev.data.message_id };
    case "answer.delta":
      if (turn.status !== "streaming") return turn;
      return {
        ...turn,
        spans: [...turn.spans, { text: ev.data.text, citations: ev.data.citations }],
        citations: mergeCitations(turn.citations, ev.data.citations),
      };
    case "answer.completed":
      if (turn.status !== "streaming") return turn;
      return {
        ...turn,
        status: "completed",
        answerType: ev.data.answer_type,
        citations: mergeCitations(turn.citations, ev.data.citations),
        pendingDocuments: ev.data.pending_documents,
      };
    case "answer.stopped":
      return { ...turn, status: "stopped" };
    case "answer.failed":
      if (turn.status !== "streaming") return turn;
      return { ...turn, status: "failed", failCode: ev.data.code };
  }
}

export function useChat(docSetId: string) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [streamingKey, setStreamingKey] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const turnsRef = useRef(turns);
  turnsRef.current = turns;

  useEffect(() => () => abortRef.current?.abort(), []);

  const update = useCallback((key: string, fn: (t: Turn) => Turn) => {
    setTurns((ts) => ts.map((t) => (t.key === key ? fn(t) : t)));
  }, []);

  const send = useCallback(
    async (question: string) => {
      const turn = newTurn(question);
      setTurns((ts) => [...ts, turn]);
      setStreamingKey(turn.key);
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        let cid = conversationId;
        if (!cid) {
          cid = (await createConversation(docSetId)).conversation_id;
          setConversationId(cid);
        }
        await streamAnswer(cid, question, (ev) => update(turn.key, (t) => applyEvent(t, ev)), controller.signal);
        // Stream đóng mà không có sự kiện kết thúc → coi là gián đoạn.
        update(turn.key, (t) => (t.status === "streaming" ? { ...t, status: "failed", failCode: "NETWORK" } : t));
      } catch (e) {
        const code = e instanceof ApiError ? e.code : controller.signal.aborted ? "ABORTED" : "NETWORK";
        update(turn.key, (t) => (t.status === "streaming" ? { ...t, status: "failed", failCode: code } : t));
      } finally {
        setStreamingKey((k) => (k === turn.key ? null : k));
      }
    },
    [conversationId, docSetId, update],
  );

  /** Dừng (US-017): ngừng hiển thị ngay, ô nhập dùng được ngay; server trả answer.stopped sau. */
  const stop = useCallback(() => {
    const key = streamingKey;
    if (!key) return;
    const turn = turnsRef.current.find((t) => t.key === key);
    update(key, (t) => ({ ...t, status: "stopped" }));
    setStreamingKey(null);
    // Giữ controller của lượt này: khi lỗi đến muộn, abortRef có thể đã trỏ sang câu hỏi mới.
    const controller = abortRef.current;
    if (turn?.messageId) {
      stopMessage(turn.messageId).catch(() => controller?.abort());
    } else {
      controller?.abort(); // chưa có message_id: hủy request
    }
  }, [streamingKey, update]);

  /** Hội thoại mới (US-016): tạo conversation mới, xóa vùng hội thoại; danh sách tài liệu giữ nguyên. */
  const newConversation = useCallback(async () => {
    if (streamingKey) stop();
    setTurns([]);
    setConversationId(null);
    const { conversation_id } = await createConversation(docSetId);
    setConversationId(conversation_id);
  }, [docSetId, stop, streamingKey]);

  const setFeedback = useCallback(
    (key: string, feedback: Turn["feedback"]) => update(key, (t) => ({ ...t, feedback })),
    [update],
  );

  /** Popover nhận 410: đánh dấu trích dẫn đã gỡ để danh sách "Nguồn" hiện "Tài liệu đã được gỡ". */
  const markCitationRemoved = useCallback((citationId: string) => {
    const strip = (c: CitationRef) => (c.citation_id === citationId ? { ...c, filename: null, document_id: null } : c);
    setTurns((ts) =>
      ts.map((t) => ({
        ...t,
        citations: t.citations.map(strip),
        spans: t.spans.map((s) => ({ ...s, citations: s.citations.map(strip) })),
      })),
    );
  }, []);

  return {
    turns,
    streaming: streamingKey !== null,
    send,
    stop,
    newConversation,
    setFeedback,
    markCitationRemoved,
  };
}
