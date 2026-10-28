import type { Turn } from "../api/types";
import { AnswerCard } from "./AnswerCard";

type Props = {
  turns: Turn[];
  onRegenerate: (question: string) => void;
  onFeedback: (key: string, feedback: Turn["feedback"]) => void;
  onCitationRemoved: (citationId: string) => void;
};

export function ChatThread({ turns, ...handlers }: Props) {
  return (
    <div className="chat-inner" aria-live="polite">
      {turns.map((t, i) => (
        <div key={t.key} className="stack" style={{ gap: "var(--sp-6)" }}>
          <p className="msg-user">{t.question}</p>
          <AnswerCard turn={t} index={i} {...handlers} />
        </div>
      ))}
    </div>
  );
}
