"""Bộ câu hỏi đánh giá nhỏ (T-15): chạy ~20 câu qua API thật, chấm tự động, ghi báo cáo.

Chạy trong container api (thư mục eval/ được mount vào /eval):
    docker compose exec api python /eval/run_eval.py --dry-run      # kiểm tra YAML + corpus, không gọi API
    docker compose exec api python /eval/run_eval.py                # chạy thật (gọi Claude ~20–30 lần)

Trước đó sinh PDF corpus trên máy host: cd web && npm run eval:corpus
Báo cáo ghi ra eval/reports/YYYY-MM-DD.md — chỉ ghi đạt/không và các ý bị thiếu, KHÔNG ghi câu trả lời đầy đủ.
"""

import argparse
import asyncio
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import httpx
import yaml

EVAL_DIR = Path(__file__).resolve().parent
TYPES = ("SC-01", "SC-02", "SC-03", "SC-04")
THRESHOLDS = {"SC-01": 0.8, "SC-02": 0.7, "SC-03": 0.75, "SC-04": 0.8}
READY_TIMEOUT_SECONDS = 15 * 60


# ---------------------------------------------------------------- đọc và kiểm tra đầu vào


def load_questions(path: Path) -> list[dict]:
    items = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(items, list):
        raise ValueError("questions.yaml phải là một danh sách")
    return items


def validate(questions: list[dict], corpus_dir: Path) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for i, q in enumerate(questions):
        qid = q.get("id") or f"#{i}"
        if qid in seen:
            errors.append(f"{qid}: id bị trùng")
        seen.add(qid)
        if q.get("type") not in TYPES:
            errors.append(f"{qid}: type phải là một trong {TYPES}")
        if not isinstance(q.get("question"), str) or not q["question"].strip():
            errors.append(f"{qid}: thiếu question")
        if not isinstance(q.get("expected", []), list):
            errors.append(f"{qid}: expected phải là danh sách")
        if not all(isinstance(h, str) for h in q.get("history", [])):
            errors.append(f"{qid}: history phải là danh sách câu hỏi")
        for s in q.get("sources", []):
            if not isinstance(s, dict) or not isinstance(s.get("file"), str) or not isinstance(s.get("page"), int):
                errors.append(f"{qid}: source sai dạng {{file, page}}: {s!r}")
            elif not (corpus_dir / s["file"]).exists():
                errors.append(f"{qid}: thiếu file corpus {s['file']} (chạy: cd web && npm run eval:corpus)")
        if q.get("type") == "SC-03" and (q.get("expected") or q.get("sources")):
            errors.append(f"{qid}: SC-03 không có expected/sources")
        if q.get("type") == "SC-04" and not q.get("history"):
            errors.append(f"{qid}: SC-04 cần history")
    if not list(corpus_dir.glob("*.pdf")):
        errors.append(f"{corpus_dir} chưa có PDF nào (chạy: cd web && npm run eval:corpus)")
    return errors


# ---------------------------------------------------------------- chấm điểm (hàm thuần)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace(".", "")).strip()


@dataclass
class Outcome:
    answer_type: str | None = None
    answer: str = ""
    citations: list[dict] = field(default_factory=list)
    failed: str | None = None
    first_token_seconds: float | None = None


@dataclass
class Score:
    passed: bool
    citations_ok: bool
    missing: list[str]


def score(q: dict, out: Outcome) -> Score:
    if q["type"] == "SC-03":
        return Score(passed=out.answer_type == "not_found", citations_ok=True, missing=[])
    answer = normalize(out.answer)
    missing = [e for e in q.get("expected", []) if normalize(e) not in answer]
    passed = out.answer_type == "answered" and not missing
    got = {(c.get("filename"), c.get("page")) for c in out.citations}
    citations_ok = all((s["file"], s["page"]) in got for s in q.get("sources", []))
    return Score(passed=passed, citations_ok=citations_ok, missing=missing)


# ---------------------------------------------------------------- gọi API


def parse_sse_lines(lines) -> list[tuple[str, dict]]:
    events, name, data = [], None, []
    for line in lines:
        if line == "":
            if name and data:
                events.append((name, json.loads("\n".join(data))))
            name, data = None, []
        elif line.startswith(":"):
            continue
        elif line.startswith("event:"):
            name = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].lstrip())
    if name and data:
        events.append((name, json.loads("\n".join(data))))
    return events


def ask(client: httpx.Client, cid: str, question: str) -> Outcome:
    out = Outcome()
    started = time.monotonic()
    with client.stream("POST", f"/api/v1/conversations/{cid}/messages", json={"question": question}) as r:
        if r.status_code != 200:
            r.read()
            out.failed = r.json().get("code", str(r.status_code))
            return out
        lines = []
        for line in r.iter_lines():
            if line.startswith("event: answer.delta") and out.first_token_seconds is None:
                out.first_token_seconds = time.monotonic() - started
            lines.append(line)
    for name, data in parse_sse_lines(lines):
        if name == "answer.delta":
            out.answer += data["text"]
        elif name == "answer.completed":
            out.answer_type = data["answer_type"]
            out.citations = data["citations"]
        elif name in ("answer.failed", "answer.stopped"):
            out.failed = data.get("code", name)
    return out


async def ensure_eval_doc_set(email: str, name: str) -> str:
    """Bộ tài liệu riêng cho đánh giá; người chạy là Quản lý bộ tài liệu (được tải lô). Không có API tạo bộ nên ghi DB."""
    from sqlalchemy import select

    from app.db import SessionLocal, engine
    from app.models import DocSet, Membership, User

    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == email))
        if user is None:
            raise SystemExit(f"Không có tài khoản {email} — chạy `python -m app.seed` trước")
        doc_set = await db.scalar(select(DocSet).where(DocSet.name == name))
        if doc_set is None:
            doc_set = DocSet(name=name)
            db.add(doc_set)
            await db.flush()
        m = await db.get(Membership, (doc_set.id, user.id))
        if m is None:
            db.add(Membership(doc_set_id=doc_set.id, user_id=user.id, role="manager"))
        else:
            m.role = "manager"
        await db.commit()
        dsid = str(doc_set.id)
    await engine.dispose()
    return dsid


def upload_corpus(client: httpx.Client, dsid: str, corpus_dir: Path) -> None:
    pdfs = sorted(corpus_dir.glob("*.pdf"))
    existing = {d["filename"]: d for d in client.get(f"/api/v1/doc-sets/{dsid}/documents").json()}
    missing = [p for p in pdfs if p.name not in existing or existing[p.name]["status"] == "failed"]
    if missing:
        client.post(f"/api/v1/doc-sets/{dsid}/classification-confirmations").raise_for_status()
        files = [("files", (p.name, p.read_bytes(), "application/pdf")) for p in missing]
        r = client.post(f"/api/v1/doc-sets/{dsid}/documents", files=files)
        r.raise_for_status()
        for res in r.json():
            if res["error_code"]:
                raise SystemExit(f"Tải {res['filename']} lỗi: {res['error_code']}")
        print(f"Đã tải lên {len(missing)} file, chờ xử lý…")

    deadline = time.monotonic() + READY_TIMEOUT_SECONDS
    names = {p.name for p in pdfs}
    while True:
        docs = [d for d in client.get(f"/api/v1/doc-sets/{dsid}/documents").json() if d["filename"] in names]
        failed = [d["filename"] for d in docs if d["status"] == "failed"]
        if failed:
            raise SystemExit(f"Xử lý lỗi: {failed}")
        if len(docs) == len(names) and all(d["status"] == "ready" for d in docs):
            return
        if time.monotonic() > deadline:
            raise SystemExit("Quá thời gian chờ tài liệu sẵn sàng")
        time.sleep(3)


# ---------------------------------------------------------------- báo cáo


def write_report(path: Path, rows: list[tuple[dict, Outcome, Score]], tau: float, model: str, fake: bool) -> str:
    lines = [
        f"# Báo cáo đánh giá — {date.today().isoformat()}",
        "",
        f"- Model: `{model}`{' (**LLM_FAKE=1 — không phải Claude thật**)' if fake else ''}",
        f"- Ngưỡng không tìm thấy τ (`RETRIEVAL_NOT_FOUND_TAU`): **{tau}**",
        f"- Số câu: {len(rows)}",
        "",
        "## Tổng hợp theo loại",
        "",
        "| Loại | Đạt | Tỷ lệ | Ngưỡng tham khảo | Trích dẫn đúng |",
        "|---|---|---|---|---|",
    ]
    for t in TYPES:
        sub = [(q, o, s) for q, o, s in rows if q["type"] == t]
        if not sub:
            continue
        ok = sum(s.passed for _, _, s in sub)
        cit = sum(s.citations_ok for _, _, s in sub)
        rate = ok / len(sub)
        mark = "✅" if rate >= THRESHOLDS[t] else "❌"
        lines.append(f"| {t} | {ok}/{len(sub)} | {rate:.0%} {mark} | ≥ {THRESHOLDS[t]:.0%} | {cit}/{len(sub)} |")
    lines += [
        "",
        "## Từng câu",
        "",
        "| Id | Loại | Đạt | Trích dẫn đúng | answer_type | Chữ đầu tiên (s) | Số trích dẫn | Ý thiếu / lỗi |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for q, o, s in rows:
        latency = f"{o.first_token_seconds:.1f}" if o.first_token_seconds is not None else "—"
        note = o.failed or ", ".join(s.missing) or ""
        lines.append(
            f"| {q['id']} | {q['type']} | {'✅' if s.passed else '❌'} | {'✅' if s.citations_ok else '❌'} "
            f"| {o.answer_type or '—'} | {latency} | {len(o.citations)} | {note} |"
        )
    lines += [
        "",
        "## Xem lại thủ công",
        "",
        "Câu không đạt được người chấm xem lại; nếu là lỗi chấm (diễn đạt khác nhưng đúng) thì ghi `manual_pass` "
        "và lý do bên dưới. Nếu SC-03 thấp hoặc câu đúng bị chặn, chỉnh `RETRIEVAL_NOT_FOUND_TAU` trong `.env` rồi chạy lại.",
        "",
        "| Id | Kết luận | Ghi chú |",
        "|---|---|---|",
        *[f"| {q['id']} |  |  |" for q, _, s in rows if not (s.passed and s.citations_ok)],
        "",
    ]
    text = "\n".join(lines)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return text


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--user", default="minh@demo.local", help="tài khoản chạy (được gán Quản lý bộ Eval)")
    ap.add_argument("--doc-set", default="Eval")
    ap.add_argument("--questions", type=Path, default=EVAL_DIR / "questions.yaml")
    ap.add_argument("--corpus", type=Path, default=EVAL_DIR / "corpus")
    ap.add_argument("--out", type=Path, default=EVAL_DIR / "reports" / f"{date.today().isoformat()}.md")
    ap.add_argument("--dry-run", action="store_true", help="chỉ kiểm tra YAML và corpus, không gọi API")
    args = ap.parse_args()

    questions = load_questions(args.questions)
    errors = validate(questions, args.corpus)
    counts = {t: sum(q.get("type") == t for q in questions) for t in TYPES}
    print(f"{len(questions)} câu hỏi: {counts}; corpus: {len(list(args.corpus.glob('*.pdf')))} PDF")
    if errors:
        print("Lỗi:\n  " + "\n  ".join(errors))
        return 1
    if args.dry_run:
        print("Dry run OK — không gọi API.")
        return 0

    from app.config import get_settings

    settings = get_settings()
    dsid = asyncio.run(ensure_eval_doc_set(args.user, args.doc_set))
    rows: list[tuple[dict, Outcome, Score]] = []
    with httpx.Client(base_url=args.base_url, timeout=httpx.Timeout(180, connect=10)) as client:
        client.post("/api/v1/auth/login", json={"email": args.user}).raise_for_status()
        upload_corpus(client, dsid, args.corpus)
        for q in questions:
            cid = client.post(f"/api/v1/doc-sets/{dsid}/conversations").json()["conversation_id"]
            for h in q.get("history", []):
                ask(client, cid, h)
            out = ask(client, cid, q["question"])
            s = score(q, out)
            rows.append((q, out, s))
            print(f"{q['id']} {q['type']}: {'ĐẠT' if s.passed else 'KHÔNG ĐẠT'} ({out.answer_type or out.failed})")

    write_report(args.out, rows, settings.retrieval_not_found_tau, settings.llm_model, settings.llm_fake)
    print(f"Đã ghi báo cáo: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
