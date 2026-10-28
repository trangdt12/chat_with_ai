import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import { ApiError } from "../api/client";
import { documentFileUrl } from "../api/documents";
import { getCitation } from "../api/qa";
import type { CitationRef } from "../api/types";
import { Icon } from "./Icon";

const POPOVER_WIDTH = 380;

/** Nút "[n]" sau mỗi đoạn có nguồn: Enter/Space mở popover, Esc đóng và trả focus về nút. */
export function CitationButton({
  citation,
  onRemoved,
}: {
  citation: CitationRef;
  onRemoved?: (citationId: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const button = useRef<HTMLButtonElement>(null);
  const label = citation.filename
    ? `Nguồn ${citation.idx}: ${citation.filename} trang ${citation.page}`
    : `Nguồn ${citation.idx}: tài liệu đã được gỡ`;

  // Ổn định qua các lần render để effect của popover không chạy lại (và không kéo focus về nút Đóng).
  const close = useCallback(() => {
    setOpen(false);
    button.current?.focus();
  }, []);

  return (
    <>
      <button
        ref={button}
        type="button"
        className={`cite${citation.filename ? "" : " removed"}`}
        aria-label={label}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((o) => !o)}
      >
        {citation.idx}
      </button>
      {open && button.current && (
        <CitationPopover citation={citation} anchor={button.current} onClose={close} onRemoved={onRemoved} />
      )}
    </>
  );
}

function position(anchor: HTMLElement): CSSProperties {
  const r = anchor.getBoundingClientRect();
  const left = Math.max(8, Math.min(r.left, window.innerWidth - POPOVER_WIDTH - 8));
  const below = r.bottom + 6;
  return below + 260 > window.innerHeight
    ? { position: "fixed", left, bottom: window.innerHeight - r.top + 6 }
    : { position: "fixed", left, top: below };
}

export function CitationPopover({
  citation,
  anchor,
  onClose,
  onRemoved,
}: {
  citation: CitationRef;
  anchor: HTMLElement;
  onClose: () => void;
  onRemoved?: (citationId: string) => void;
}) {
  const box = useRef<HTMLDivElement>(null);
  const closeBtn = useRef<HTMLButtonElement>(null);
  const [style, setStyle] = useState<CSSProperties>(() => position(anchor));

  const detail = useQuery({
    queryKey: ["citation", citation.citation_id],
    queryFn: () => getCitation(citation.citation_id),
    retry: false,
    staleTime: 60_000,
  });
  const removed =
    !citation.filename || (detail.error instanceof ApiError && detail.error.code === "DOCUMENT_REMOVED");

  useEffect(() => {
    if (detail.error instanceof ApiError && detail.error.code === "DOCUMENT_REMOVED" && citation.filename) {
      onRemoved?.(citation.citation_id);
    }
  }, [detail.error, citation, onRemoved]);

  useLayoutEffect(() => setStyle(position(anchor)), [anchor]);

  useEffect(() => closeBtn.current?.focus(), []); // chỉ khi mở

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    }
    function onPointer(e: MouseEvent) {
      const target = e.target as Node;
      if (!box.current?.contains(target) && !anchor.contains(target)) onClose();
    }
    function onScroll() {
      setStyle(position(anchor));
    }
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onPointer);
    window.addEventListener("resize", onScroll);
    document.addEventListener("scroll", onScroll, true);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onPointer);
      window.removeEventListener("resize", onScroll);
      document.removeEventListener("scroll", onScroll, true);
    };
  }, [anchor, onClose]);

  const page = detail.data?.page ?? citation.page;
  const filename = detail.data?.filename ?? citation.filename;

  return createPortal(
    <div ref={box} className="popover" style={style} role="dialog" aria-labelledby={`pop-${citation.citation_id}`}>
      <div className="popover-head">
        <div className="popover-file" id={`pop-${citation.citation_id}`}>
          <Icon name="file" small />
          <span>{removed ? `Nguồn [${citation.idx}]` : `${filename} · trang ${page}`}</span>
        </div>
        <button ref={closeBtn} className="btn btn-ghost btn-icon btn-sm" type="button" aria-label="Đóng" onClick={onClose}>
          <Icon name="x" small />
        </button>
      </div>

      {removed ? (
        <div className="removed-box">
          <Icon name="trash" small />
          <div>
            <strong>Tài liệu đã được gỡ khỏi bộ tài liệu.</strong>
            <br />
            Không còn xem được đoạn trích hay tài liệu gốc. Câu trả lời này được giữ nguyên để tham khảo lịch sử.
          </div>
        </div>
      ) : detail.isPending ? (
        <div className="stack" aria-busy="true">
          <div className="skeleton" />
          <div className="skeleton" style={{ width: "70%" }} />
        </div>
      ) : detail.isError ? (
        <p className="small muted">Không tải được đoạn trích. Hãy thử lại.</p>
      ) : (
        <>
          <blockquote className="popover-quote" style={{ margin: 0 }}>
            “{detail.data.snippet}”
          </blockquote>
          <div className="popover-foot">
            <span className="small muted">Đoạn trích tối đa 300 ký tự</span>
            <button
              className="btn btn-secondary btn-sm"
              type="button"
              onClick={() => window.open(documentFileUrl(detail.data.document_id, page), "_blank", "noopener")}
            >
              Mở tài liệu gốc tại trang {page}
              <Icon name="external" small />
            </button>
          </div>
        </>
      )}
    </div>,
    document.body,
  );
}
