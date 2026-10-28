import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { Icon } from "./Icon";

type ToastKind = "info" | "success" | "danger";
type ToastItem = { id: number; kind: ToastKind; text: string };
type ToastFn = (text: string, kind?: ToastKind) => void;

const ToastContext = createContext<ToastFn>(() => {});

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: number) => setItems((xs) => xs.filter((t) => t.id !== id)), []);

  const toast = useCallback<ToastFn>(
    (text, kind = "info") => {
      const id = nextId++;
      setItems((xs) => [...xs, { id, kind, text }]);
      window.setTimeout(() => dismiss(id), 6000);
    },
    [dismiss],
  );

  const value = useMemo(() => toast, [toast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-region" role="status" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} className={`toast ${t.kind === "info" ? "" : `toast-${t.kind}`}`}>
            <Icon name={t.kind === "danger" ? "alert" : t.kind === "success" ? "check" : "info"} />
            <span style={{ flex: 1 }}>{t.text}</span>
            <button className="btn btn-ghost btn-icon btn-sm" type="button" aria-label="Đóng thông báo" onClick={() => dismiss(t.id)}>
              <Icon name="x" small />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastFn {
  return useContext(ToastContext);
}
