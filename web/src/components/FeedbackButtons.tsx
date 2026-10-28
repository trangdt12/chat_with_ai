import { useState } from "react";
import { submitFeedback } from "../api/qa";
import type { FeedbackReason, Turn } from "../api/types";
import { Icon } from "./Icon";
import { useToast } from "./Toasts";

const REASONS: { value: FeedbackReason; label: string }[] = [
  { value: "wrong", label: "Sai thông tin" },
  { value: "missing", label: "Thiếu thông tin" },
  { value: "wrong_source", label: "Nguồn không đúng" },
  { value: "other", label: "Lý do khác" },
];

type Props = {
  messageId: string;
  value: Turn["feedback"];
  onChange: (feedback: Turn["feedback"]) => void;
};

/** US-015: 👍 gửi ngay; 👎 mở danh sách lý do rồi gửi. Bấm nút còn lại thì gửi đè. */
export function FeedbackButtons({ messageId, value, onChange }: Props) {
  const toast = useToast();
  const [reasonsOpen, setReasonsOpen] = useState(false);
  const [reason, setReason] = useState<FeedbackReason>(value?.reason ?? "wrong");
  const [busy, setBusy] = useState(false);

  async function send(rating: "up" | "down", why: FeedbackReason | null) {
    setBusy(true);
    try {
      await submitFeedback(messageId, rating, why);
      onChange({ rating, reason: why });
      setReasonsOpen(false);
    } catch {
      toast("Không gửi được đánh giá, thử lại", "danger"); // giữ trạng thái cũ
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        className="btn btn-ghost btn-sm"
        type="button"
        aria-pressed={value?.rating === "up"}
        aria-label="Câu trả lời hữu ích"
        disabled={busy}
        onClick={() => send("up", null)}
      >
        <Icon name="up" small />
      </button>
      <button
        className="btn btn-ghost btn-sm"
        type="button"
        aria-pressed={value?.rating === "down"}
        aria-label="Câu trả lời chưa tốt"
        aria-expanded={reasonsOpen}
        disabled={busy}
        onClick={() => setReasonsOpen((o) => !o)}
      >
        <Icon name="down" small />
      </button>
      {reasonsOpen && (
        <fieldset className="reasons" style={{ flexBasis: "100%" }}>
          <legend>Vì sao câu trả lời chưa tốt?</legend>
          {REASONS.map((r) => (
            <label key={r.value} className="chip">
              <input
                type="radio"
                name={`reason-${messageId}`}
                value={r.value}
                checked={reason === r.value}
                onChange={() => setReason(r.value)}
              />
              {r.label}
            </label>
          ))}
          <button className="btn btn-primary btn-sm" type="button" disabled={busy} onClick={() => send("down", reason)}>
            Gửi đánh giá
          </button>
        </fieldset>
      )}
    </>
  );
}
