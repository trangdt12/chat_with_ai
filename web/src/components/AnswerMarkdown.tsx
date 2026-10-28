import { createContext, useContext, useMemo } from "react";
import Markdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import type { CitationRef, Span } from "../api/types";
import { CitationButton } from "./CitationPopover";

// Backend không chèn "[n]" vào text (README §2.6): FE ghép text các span, đặt dấu mốc sau mỗi span có nguồn,
// render markdown rồi thay dấu mốc bằng nút trích dẫn. Dùng ký tự vùng riêng (Private Use) để không đụng nội dung.
const OPEN = "";
const CLOSE = "";
const MARK_RE = /(\d+)/g;

export function spansToMarkdown(spans: Span[]): string {
  return spans
    .map((s) => {
      const marks = s.citations.map((c) => `${OPEN}${c.idx}${CLOSE}`).join("");
      // Dấu mốc đặt trước khoảng trắng/xuống dòng cuối span để dính vào câu vừa trích.
      const m = /\s*$/.exec(s.text);
      const tail = m ? m[0] : "";
      return s.text.slice(0, s.text.length - tail.length) + marks + tail;
    })
    .join("");
}

type HastNode = { type: string; value?: string; tagName?: string; properties?: Record<string, unknown>; children?: HastNode[] };

/** rehype plugin: tách text node chứa dấu mốc thành text + <sup data-cite="n">. */
function rehypeCitations() {
  function walk(node: HastNode) {
    if (!node.children) return;
    const out: HastNode[] = [];
    for (const child of node.children) {
      if (child.type === "text" && child.value && child.value.includes(OPEN)) {
        let last = 0;
        for (const m of child.value.matchAll(MARK_RE)) {
          if (m.index! > last) out.push({ type: "text", value: child.value.slice(last, m.index) });
          out.push({ type: "element", tagName: "sup", properties: { dataCite: m[1] }, children: [] });
          last = m.index! + m[0].length;
        }
        if (last < child.value.length) out.push({ type: "text", value: child.value.slice(last) });
      } else {
        walk(child);
        out.push(child);
      }
    }
    node.children = out;
  }
  return (tree: unknown) => walk(tree as HastNode);
}

// Chỉ cho phép đoạn, danh sách, in đậm/nghiêng, bảng (T-11 §2.2). Không bật rehype-raw: HTML hiển thị dạng chữ.
const ALLOWED = ["p", "br", "ul", "ol", "li", "strong", "em", "table", "thead", "tbody", "tr", "th", "td", "sup"];

type Props = {
  spans: Span[];
  citations: CitationRef[];
  streaming?: boolean;
  onCitationRemoved?: (citationId: string) => void;
};

type CiteContextValue = { byIdx: Map<string, CitationRef>; onRemoved?: (citationId: string) => void };
const CiteContext = createContext<CiteContextValue>({ byIdx: new Map() });

// Component ổn định (khai báo ở module): nếu tạo mới mỗi lần render, React sẽ gắn lại nút [n]
// và popover đang mở bị đóng mỗi khi danh sách tài liệu polling hoặc có delta mới.
function Sup({ node }: { node?: { properties?: Record<string, unknown> } }) {
  const { byIdx, onRemoved } = useContext(CiteContext);
  const citation = byIdx.get(String(node?.properties?.dataCite ?? ""));
  return citation ? <CitationButton citation={citation} onRemoved={onRemoved} /> : null;
}

const COMPONENTS = { sup: Sup } as Components;
const REMARK_PLUGINS = [remarkGfm];
const REHYPE_PLUGINS = [rehypeCitations];

export function AnswerMarkdown({ spans, citations, streaming, onCitationRemoved }: Props) {
  const value = useMemo(
    () => ({ byIdx: new Map(citations.map((c) => [String(c.idx), c])), onRemoved: onCitationRemoved }),
    [citations, onCitationRemoved],
  );
  return (
    <div className="answer-body">
      <CiteContext.Provider value={value}>
        <Markdown
          remarkPlugins={REMARK_PLUGINS}
          rehypePlugins={REHYPE_PLUGINS}
          allowedElements={ALLOWED}
          unwrapDisallowed
          skipHtml={false}
          components={COMPONENTS}
        >
          {spansToMarkdown(spans)}
        </Markdown>
      </CiteContext.Provider>
      {streaming && <span className="caret" aria-hidden="true" />}
    </div>
  );
}
