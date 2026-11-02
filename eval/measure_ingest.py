"""Đo thời gian xử lý tài liệu và chuỗi trạng thái (docs/test/test-cases.yaml TC-005, TC-006, TC-007).

Chạy trong container api khi stack đang chạy (worker bật):
    docker compose exec api python /eval/measure_ingest.py --pages 3 --runs 1 --poll 0.2 --json /eval/reports/f.json
    docker compose exec api python /eval/measure_ingest.py --pages 50 --runs 3 --json /eval/reports/ingest-50.json
    docker compose exec api python /eval/measure_ingest.py --pages 200 --runs 3 --json /eval/reports/ingest-200.json

Mỗi lần đo: xóa tài liệu cũ của bộ "Perf", chờ hàng đợi worker rỗng, tải 1 PDF n trang chữ dày,
đo t = lúc GET /documents thấy `ready` − lúc API tải lên trả 200. Giới hạn mặc định theo NFR-003:
≤ 120 s nếu n ≤ 50 trang, ≤ 480 s nếu n ≤ 200 trang. PASS ⇔ mọi lần đều đạt (không lấy trung bình).
"""

import argparse
import asyncio
import json
import os
import platform
import shutil
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx
from run_eval import ensure_eval_doc_set
from sqlalchemy import delete, func, select

from app.config import get_settings
from app.db import SessionLocal, engine
from app.documents import storage
from app.models import Document
from tests.pdf_factory import make_pdf

ORDER = ["uploaded", "processing", "ready"]
WORDS = (
    "hop dong khung thoi han thanh toan nghiem thu bao hanh trien khai dao tao phu luc bao gia dich vu "
    "cong ty ben mua ben ban hoa don gia tri dieu khoan trach nhiem bao mat du lieu ke hoach giai doan"
).split()


def nfr_limit(pages: int) -> int:
    return 120 if pages <= 50 else 480


def dense_pages(n: int, chars: int = 1500) -> list[str]:
    """Chữ Latin không dấu, ~`chars` ký tự/trang, mỗi trang khác nhau (tất định)."""
    pages = []
    for p in range(1, n + 1):
        words, i = [f"Trang {p}."], p
        while sum(len(w) + 1 for w in words) < chars:
            words.append(WORDS[(i * 7 + len(words)) % len(WORDS)])
            if len(words) % 15 == 0:
                words[-1] += "."
            i += 1
        pages.append(" ".join(words))
    return pages


def dedup(seq: list[str]) -> list[str]:
    return [s for i, s in enumerate(seq) if i == 0 or s != seq[i - 1]]


def is_subsequence(seq: list[str], order: list[str]) -> bool:
    it = iter(order)
    return all(s in it for s in seq)


# Mỗi hàm DB chạy trong asyncio.run riêng nên phải dispose engine trước khi event loop đóng.


async def clear_doc_set(dsid: str) -> None:
    ds = uuid.UUID(dsid)
    async with SessionLocal() as db:
        await db.execute(delete(Document).where(Document.doc_set_id == ds))  # chunks xóa theo FK cascade
        await db.commit()
    await engine.dispose()
    shutil.rmtree(storage.file_path_for(ds, ds).parent, ignore_errors=True)


async def queue_size() -> int:
    async with SessionLocal() as db:
        n = await db.scalar(
            select(func.count()).select_from(Document).where(Document.status.in_(("uploaded", "processing")))
        )
    await engine.dispose()
    return n


def wait_idle(timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if asyncio.run(queue_size()) == 0:
            return True
        time.sleep(1)
    return False


def measure_once(client: httpx.Client, dsid: str, pdf: bytes, pages: int, poll: float, timeout: float) -> dict:
    client.post(f"/api/v1/doc-sets/{dsid}/classification-confirmations").raise_for_status()
    r = client.post(
        f"/api/v1/doc-sets/{dsid}/documents", files=[("files", (f"perf_{pages}p.pdf", pdf, "application/pdf"))]
    )
    r.raise_for_status()
    t0 = time.monotonic()
    [res] = r.json()
    if res["error_code"]:
        return {"final": "rejected", "error_code": res["error_code"]}

    statuses, progress, doc = [], [], None
    while time.monotonic() - t0 < timeout:
        doc = next(d for d in client.get(f"/api/v1/doc-sets/{dsid}/documents").json() if d["id"] == res["id"])
        statuses.append(doc["status"])
        progress.append(doc["progress"])
        if doc["status"] in ("ready", "failed"):
            break
        time.sleep(poll)
    elapsed = time.monotonic() - t0
    seq = dedup(statuses)
    return {
        "final": doc["status"] if doc else None,
        "error_code": doc["error_code"] if doc else None,
        "pages": doc["pages"] if doc else None,
        "seconds_to_ready": round(elapsed, 2) if doc and doc["status"] == "ready" else None,
        "sequence": seq,
        "sequence_ok": is_subsequence(seq, ORDER),
        "progress_monotonic": all(a <= b for a, b in zip(progress, progress[1:], strict=False)),
        "final_progress": progress[-1] if progress else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--user", default="lan@demo.local")
    ap.add_argument("--doc-set", default="Perf")
    ap.add_argument("--pages", type=int, required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--poll", type=float, default=1.0)
    ap.add_argument("--limit", type=float, help="giới hạn giây (mặc định theo NFR-003)")
    ap.add_argument("--timeout", type=float, help="ngừng chờ sau ngần này giây (mặc định 2 × limit)")
    ap.add_argument("--commit", default=os.environ.get("GIT_COMMIT", ""), help="commit đang đo, ghi vào báo cáo")
    ap.add_argument("--json", type=Path, required=True)
    args = ap.parse_args()

    limit = args.limit or nfr_limit(args.pages)
    timeout = args.timeout or 2 * limit
    settings = get_settings()
    pdf = make_pdf(dense_pages(args.pages))
    dsid = asyncio.run(ensure_eval_doc_set(args.user, args.doc_set))

    runs = []
    with httpx.Client(base_url=args.base_url, timeout=httpx.Timeout(120, connect=10)) as client:
        client.post("/api/v1/auth/login", json={"email": args.user}).raise_for_status()
        for i in range(args.runs):
            asyncio.run(clear_doc_set(dsid))
            if not wait_idle(600):
                print("BLOCKED: hàng đợi worker không rỗng sau 600 s", file=sys.stderr)
                return 2
            run = measure_once(client, dsid, pdf, args.pages, args.poll, timeout)
            run["pages_ok"] = run.get("pages") == args.pages
            run["pass"] = (
                run["final"] == "ready"
                and run["pages_ok"]
                and run["sequence_ok"]
                and run["progress_monotonic"]
                and run["final_progress"] == 100
                and run["seconds_to_ready"] <= limit
            )
            runs.append(run)
            print(f"lần {i + 1}: {run['final']} {run.get('seconds_to_ready')} s, chuỗi {run.get('sequence')}")
        asyncio.run(clear_doc_set(dsid))

    meminfo = Path("/proc/meminfo").read_text().splitlines()
    mem_kb = next((int(ln.split()[1]) for ln in meminfo if ln.startswith("MemTotal")), 0)
    result = {
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "commit": args.commit,
        "pages": args.pages,
        "pdf_bytes": len(pdf),
        "limit_seconds": limit,
        "embed_fake": settings.embed_fake,
        "embed_model": settings.embed_model,
        "machine": {"cpu_count": os.cpu_count(), "mem_gb": round(mem_kb / 1024**2, 1), "platform": platform.platform()},
        "runs": runs,
        "all_pass": len(runs) == args.runs and all(r["pass"] for r in runs),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"all_pass={result['all_pass']} → {args.json}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
