import type { Turn } from "../api/types";
import { AnswerMarkdown } from "./AnswerMarkdown";
import { answerToPlainText } from "./copy";
import { FeedbackButtons } from "./FeedbackButtons";
import { Icon } from "./Icon";
import { useToast } from "./Toasts";

type Props = {
  turn: Turn;
  index: number;
  onRegenerate: (question: string) => void;
  onFeedback: (key: string, feedback: Turn["feedback"]) => void;
  onCitationRemoved: (citationId: string) => void;
};

/** Câu trả lời một lượt: nội dung + [n], danh sách nguồn, ghi chú tài liệu chưa sẵn sàng, trạng thái, thao tác. */
export function AnswerCard({ turn, index, onRegenerate, onFeedback, onCitationRemoved }: Props) {
  const toast = useToast();
  const hasBody = turn.spans.length > 0;
  const completed = turn.status === "completed";
  const notFound = completed && turn.answerType === "not_found";
  const showActions = completed && !notFound && hasBody;

  async function copy() {
    try {
      await navigator.clipboard.writeText(answerToPlainText(turn.spans, turn.citations));
      toast("Đã sao chép câu trả lời kèm nguồn. Nhớ đối chiếu nguồn trước khi gửi cho đối tác.", "success");
    } catch {
      toast("Không sao chép được. Hãy chọn và sao chép thủ công.", "danger");
    }
  }

  return (
    <article className="msg-assistant" aria-label={`Câu trả lời lượt ${index + 1}`} aria-busy={turn.status === "streaming"}>
      <div className="assistant-mark" aria-hidden="true">
        AI
      </div>
      <div className="answer">
        {turn.status === "streaming" && !hasBody && (
          <div className="answer-status">
            <span className="typing" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
            Đang trả lời…
          </div>
        )}

        {completed && turn.answerType === "clarification" && (
          <div className="answer-status">
            <Icon name="list" small />
            Tài liệu có nhiều đáp án — bạn muốn hỏi trường hợp nào?
          </div>
        )}

        {notFound && (
          <div className="banner banner-info">
            <Icon name="search" />
            <div>
              <strong className="banner-title">Không tìm thấy thông tin này trong các tài liệu đã tải lên.</strong>
              Bạn có thể thử:
              <ul style={{ margin: "var(--sp-1) 0 0", paddingLeft: "var(--sp-5)" }}>
                <li>Diễn đạt lại câu hỏi bằng từ ngữ có trong tài liệu.</li>
                <li>Kiểm tra tài liệu liên quan đã được tải lên và ở trạng thái “Sẵn sàng” chưa.</li>
              </ul>
            </div>
          </div>
        )}

        {hasBody && !notFound && (
          <AnswerMarkdown
            spans={turn.spans}
            citations={turn.citations}
            streaming={turn.status === "streaming"}
            onCitationRemoved={onCitationRemoved}
          />
        )}

        {(completed || turn.status === "stopped") && turn.citations.length > 0 && !notFound && (
          <div className="sources">
            <div className="sources-title">Nguồn</div>
            <ol>
              {turn.citations.map((c) => (
                <li key={c.idx} value={c.idx}>
                  {c.filename ? (
                    `${c.filename} · trang ${c.page}`
                  ) : (
                    <span className="muted">Tài liệu đã được gỡ</span>
                  )}
                </li>
              ))}
            </ol>
          </div>
        )}

        {completed && turn.pendingDocuments.length > 0 && (
          <div className="banner banner-info pending-note">
            <Icon name="clock" />
            <div>
              Tài liệu sau chưa được dùng để trả lời vì đang xử lý:{" "}
              <strong>{turn.pendingDocuments.map((d) => d.filename).join(", ")}</strong>
            </div>
          </div>
        )}

        {turn.status === "stopped" && (
          <div className="answer-status">
            <Icon name="stop" small />
            Đã dừng theo yêu cầu của bạn · câu trả lời chưa đầy đủ
          </div>
        )}

        {turn.status === "failed" && (
          <div className="banner banner-warning" role="alert">
            <Icon name="alert" />
            <div style={{ flex: 1 }}>
              <strong className="banner-title">Câu trả lời bị gián đoạn — chưa hoàn tất</strong>
              {turn.failCode === "NO_READY_DOCUMENTS"
                ? "Bộ tài liệu chưa có tài liệu nào ở trạng thái “Sẵn sàng”."
                : "Mất kết nối hoặc hệ thống đang bận. Phần đã hiển thị chưa đầy đủ, đừng dùng để gửi đối tác."}
            </div>
            <button className="btn btn-secondary btn-sm" type="button" onClick={() => onRegenerate(turn.question)}>
              <Icon name="refresh" small />
              Tạo lại câu trả lời
            </button>
          </div>
        )}

        {showActions && turn.messageId && (
          <div className="answer-actions" role="group" aria-label="Thao tác với câu trả lời" style={{ flexWrap: "wrap" }}>
            <FeedbackButtons
              messageId={turn.messageId}
              value={turn.feedback}
              onChange={(fb) => onFeedback(turn.key, fb)}
            />
            <button className="btn btn-ghost btn-sm" type="button" onClick={copy}>
              <Icon name="copy" small />
              Sao chép kèm nguồn
            </button>
          </div>
        )}
      </div>
    </article>
  );
}
