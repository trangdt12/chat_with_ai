"""Kiểm tra trích dẫn của một lượt run_eval.py (docs/test/test-cases.yaml TC-028, TC-030).

Chạy trong container api, ngay sau run_eval.py và trước khi reset DB:
    docker compose exec api python /eval/check_grounding.py --run /eval/reports/2026-10-28.json
        → <run>-grounding.json  (AC-US009-3a: đoạn trích có nằm trên đúng trang không)
    docker compose exec api python /eval/check_grounding.py --run /eval/reports/2026-10-28.json --export-review
        → thêm <run>-grounding-review.csv để người chấm điền cột supports = yes/no (AC-US009-3b)
    docker compose exec api python /eval/check_grounding.py --run /eval/reports/2026-10-28.json --score-review
        → chấm CSV đã điền, in verdict JSON

PASS 3a ⇔ turns_checked ≥ --min-turns và không có violation. PASS 3b ⇔ đủ dòng, mọi ô yes/no, không có "no".
CSV có nội dung câu trả lời trên corpus tự soạn — không commit (.gitignore).
"""

import argparse
import asyncio
import csv
import json
import sys
import uuid
from pathlib import Path

from pypdf import PdfReader
from sqlalchemy import select

from app.db import SessionLocal, engine
from app.ingestion.chunker import normalize_page
from app.models import Citation, Document

REVIEW_FIELDS = ["question_id", "message_id", "idx", "file", "page", "span_text", "snippet", "supports"]


def norm(text: str) -> str:
    return " ".join(normalize_page(text).split()).lower()


async def load_citations(ids: list[str]) -> dict[str, tuple[Citation, str | None]]:
    """citation_id → (Citation, file_path của tài liệu hoặc None nếu đã gỡ)."""
    async with SessionLocal() as db:
        rows = await db.execute(
            select(Citation, Document.file_path)
            .outerjoin(Document, Document.id == Citation.document_id)
            .where(Citation.id.in_([uuid.UUID(i) for i in ids]))
        )
        found = {str(c.id): (c, path) for c, path in rows.all()}
    await engine.dispose()
    return found


def check(run: dict, cits: dict[str, tuple[Citation, str | None]], min_turns: int) -> dict:
    readers: dict[str, PdfReader] = {}
    violations, turns, checked = [], 0, 0
    for qid, row in run["rows"].items():
        if row["answer_type"] != "answered":
            continue
        turns += 1
        for c in row["citations"]:
            cit, path = cits.get(c["citation_id"], (None, None))
            if cit is None or path is None or not cit.snippet:
                violations.append({"question_id": qid, "citation_id": c["citation_id"], "reason": "missing"})
                continue
            reader = readers.setdefault(path, PdfReader(path))
            page_text = reader.pages[cit.page - 1].extract_text() if 1 <= cit.page <= len(reader.pages) else ""
            checked += 1
            if norm(cit.snippet) not in norm(page_text):
                violations.append(
                    {
                        "question_id": qid,
                        "citation_id": c["citation_id"],
                        "file": cit.filename,
                        "page": cit.page,
                        "reason": "snippet_not_on_page",
                    }
                )
    return {
        "turns_checked": turns,
        "citations_checked": checked,
        "violations": violations,
        "pass": turns >= min_turns and not violations,
    }


def review_pairs(spans_doc: list[dict], cits: dict[str, tuple[Citation, str | None]]) -> list[dict]:
    """Mỗi cặp (đoạn câu trả lời có trích dẫn, trích dẫn) là một dòng; câu nối không nguồn bị bỏ qua."""
    rows = []
    for turn in spans_doc:
        for span in turn["spans"]:
            for cid in span["citation_ids"]:
                cit, _ = cits.get(cid, (None, None))
                rows.append(
                    {
                        "question_id": turn["question_id"],
                        "message_id": turn["message_id"],
                        "idx": cit.idx if cit else "",
                        "file": cit.filename if cit else "",
                        "page": cit.page if cit else "",
                        "span_text": span["text"].strip(),
                        "snippet": (cit.snippet or "") if cit else "",
                        "supports": "",
                    }
                )
    return rows


def score_review(csv_path: Path, expected_rows: int) -> dict:
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    values = [(r.get("supports") or "").strip().lower() for r in rows]
    result = {
        "rows": len(rows),
        "expected_rows": expected_rows,
        "blank_or_invalid": sum(v not in ("yes", "no") for v in values),
        "no_count": values.count("no"),
    }
    result["pass"] = result["rows"] == expected_rows and result["blank_or_invalid"] == 0 and result["no_count"] == 0
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True, help="file JSON do run_eval.py ghi")
    ap.add_argument("--min-turns", type=int, default=16)
    ap.add_argument("--export-review", action="store_true")
    ap.add_argument("--score-review", action="store_true")
    args = ap.parse_args()

    run = json.loads(args.run.read_text(encoding="utf-8"))
    spans_path = args.run.with_name(f"{args.run.stem}-spans.json")
    review_path = args.run.with_name(f"{args.run.stem}-grounding-review.csv")
    spans_doc = json.loads(spans_path.read_text(encoding="utf-8")) if spans_path.exists() else []

    ids = [c["citation_id"] for r in run["rows"].values() for c in r["citations"]]
    ids += [cid for t in spans_doc for s in t["spans"] for cid in s["citation_ids"]]
    cits = asyncio.run(load_citations(sorted(set(ids)))) if ids else {}

    if args.score_review:
        result = score_review(review_path, len(review_pairs(spans_doc, cits)))
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["pass"] else 1

    result = check(run, cits, args.min_turns)
    out = args.run.with_name(f"{args.run.stem}-grounding.json")
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps({k: v for k, v in result.items() if k != "violations"} | {"violations": len(result["violations"])})
    )

    if args.export_review:
        if not spans_doc:
            print(f"Không có {spans_path} — chạy lại run_eval.py", file=sys.stderr)
            return 1
        with review_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
            w.writeheader()
            w.writerows(review_pairs(spans_doc, cits))
        print(f"Đã ghi {review_path} — điền cột supports (yes/no) rồi chạy --score-review")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
