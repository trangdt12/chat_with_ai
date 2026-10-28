import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { peekDraft, setDraftGetter, takeDraft } from "../auth/draftStore";
import { QUESTION_COUNTER_FROM, QUESTION_MAX_CHARS } from "../config";
import { Icon } from "./Icon";

type Props = {
  streaming: boolean;
  readyCount: number;
  hasDocuments: boolean;
  onSend: (question: string) => void;
  onStop: () => void;
};

/** UI-006/007: Enter gửi, Shift+Enter xuống dòng; nút Gửi ↔ Dừng; giữ bản nháp khi phiên hết hạn. */
export function Composer({ streaming, readyCount, hasDocuments, onSend, onStop }: Props) {
  const [value, setValue] = useState(peekDraft); // khôi phục câu hỏi sau khi đăng nhập lại (AC-US012-2)
  const valueRef = useRef(value);
  valueRef.current = value;
  const textarea = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    takeDraft(); // đã đổ vào ô nhập — xóa để lần sau không hiện lại
    setDraftGetter(() => valueRef.current);
    return () => setDraftGetter(null);
  }, []);

  const trimmed = value.trim();
  const remaining = QUESTION_MAX_CHARS - value.length;
  const noReady = readyCount === 0;
  const canSend = !streaming && !noReady && trimmed.length > 0 && remaining >= 0;

  function submit(e?: FormEvent) {
    e?.preventDefault();
    if (!canSend) return;
    onSend(trimmed);
    setValue("");
    textarea.current?.focus();
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Bỏ qua Enter khi bộ gõ tiếng Việt đang ghép chữ.
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  }

  const hint = !hasDocuments
    ? "Chưa có tài liệu sẵn sàng"
    : noReady
      ? "Nút Gửi sẽ bật khi có tài liệu sẵn sàng"
      : "Enter để gửi · Shift+Enter để xuống dòng";

  return (
    <div className="composer-wrap">
      <form className="composer" onSubmit={submit}>
        <label htmlFor="q" className="sr-only">
          Câu hỏi về tài liệu
        </label>
        <textarea
          id="q"
          ref={textarea}
          rows={2}
          value={value}
          disabled={!hasDocuments}
          placeholder={hasDocuments ? "Đặt câu hỏi về tài liệu…" : "Hãy tải tài liệu lên trước khi đặt câu hỏi"}
          aria-describedby="composer-hint"
          aria-invalid={remaining < 0 || undefined}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <div className="composer-row">
          <span id="composer-hint" className="small muted">
            {hint}
          </span>
          <span className="row">
            {remaining <= QUESTION_COUNTER_FROM && (
              <span className={`counter${remaining < 0 ? " over" : ""}`} aria-live="polite">
                {remaining < 0 ? `Vượt ${-remaining} ký tự` : `Còn ${remaining} ký tự`}
              </span>
            )}
            {streaming ? (
              <button className="btn btn-stop" type="button" onClick={onStop}>
                <Icon name="stop" small />
                Dừng
              </button>
            ) : (
              <button className="btn btn-primary" type="submit" disabled={!canSend}>
                <Icon name="send" small />
                Gửi
              </button>
            )}
          </span>
        </div>
      </form>
      <p className="grounding">
        <Icon name="info" small />
        Câu trả lời chỉ dựa trên tài liệu đã tải lên. Hãy đối chiếu nguồn trước khi gửi cho đối tác.
      </p>
    </div>
  );
}
