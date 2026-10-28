import { apiFetch, jsonBody } from "./client";
import type { CitationDetail, FeedbackRating, FeedbackReason } from "./types";

export function createConversation(dsid: string): Promise<{ conversation_id: string }> {
  return apiFetch(`/doc-sets/${dsid}/conversations`, { method: "POST" });
}

export function stopMessage(messageId: string): Promise<void> {
  return apiFetch(`/messages/${messageId}/stop`, { method: "POST" });
}

export function getCitation(citationId: string): Promise<CitationDetail> {
  // 410 DOCUMENT_REMOVED do popover tự hiển thị — không phải bị thu hồi quyền.
  return apiFetch(`/citations/${citationId}`);
}

export function submitFeedback(
  messageId: string,
  rating: FeedbackRating,
  reason: FeedbackReason | null,
): Promise<{ turn_id: string; rating: FeedbackRating; reason: FeedbackReason | null }> {
  return apiFetch(`/messages/${messageId}/feedback`, { method: "PUT", ...jsonBody({ rating, reason }) });
}
