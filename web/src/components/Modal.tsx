import { useEffect, useRef, type FormEvent, type KeyboardEvent, type ReactNode, type RefObject } from "react";

type Props = {
  titleId: string;
  descriptionId?: string;
  role?: "dialog" | "alertdialog";
  onClose: () => void;
  onSubmit?: () => void;
  /** Phần tử nhận focus khi mở (mặc định: phần tử focus được đầu tiên). */
  initialFocus?: RefObject<HTMLElement | null>;
  children: ReactNode;
};

const FOCUSABLE = "button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled])";

/** Hộp thoại modal: focus nằm trong hộp thoại, Esc đóng, trả focus về chỗ cũ khi đóng. */
export function Modal({ titleId, descriptionId, role = "dialog", onClose, onSubmit, initialFocus, children }: Props) {
  const box = useRef<HTMLFormElement>(null);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    (initialFocus?.current ?? box.current?.querySelector<HTMLElement>(FOCUSABLE))?.focus();
    return () => previous?.focus?.();
  }, []);

  function onKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
      return;
    }
    if (e.key !== "Tab" || !box.current) return;
    const items = Array.from(box.current.querySelectorAll<HTMLElement>(FOCUSABLE));
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    onSubmit?.();
  }

  return (
    <div className="overlay" onKeyDown={onKeyDown}>
      <form
        ref={box}
        className="dialog"
        role={role}
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        onSubmit={submit}
        noValidate
      >
        {children}
      </form>
    </div>
  );
}
