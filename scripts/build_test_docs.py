"""Sinh docs/test-cases.md và docs/traceability.md từ nguồn sự thật.

Nguồn:
  docs/test/01-pham-vi-va-ac.md    AC đã chốt (bảng "| **AC-…** |")
  docs/test/test-cases.yaml        định nghĩa PASS/FAIL của từng TC (viết trước khi chạy)
  reports/<lượt>/                  kết quả thật của scripts/run-tests.sh (junit, results.json, ingest-fake.json)
  docs/bugs/BUG-*.md               ticket cho TC FAIL (dòng "TC: TC-xxx")

Chạy (host không cần Python — dùng image api):
  docker compose run --rm --no-deps -v "$PWD:/repo" -w /repo api python scripts/build_test_docs.py

Exit code 1 nếu: AC trong phạm vi không có TC, TC không trỏ về AC, hoặc TC FAIL không có bug ticket.
"""

import json
import re
import shlex
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPORTS = ROOT / "reports"

STORIES = {
    "US-001": "Tải một file PDF lên",
    "US-009": "Trích dẫn tên tài liệu và số trang",
}
LAYER_NAME = {"U": "Unit", "I": "API tích hợp", "E": "E2E Playwright", "Q": "Chất lượng (Claude thật)",
              "P": "Hiệu năng"}
BLOCKED_REASON = {
    "Q": "cần hồ sơ REAL (Claude thật, có phí) và người chấm — không chạy trong CI",
    "P": "cần bge-m3 thật và máy tham chiếu (OI-T3) — không chạy trong CI",
}


# ---------------------------------------------------------------- nguồn
def load_acs() -> dict[str, str]:
    acs = {}
    for line in (DOCS / "test/01-pham-vi-va-ac.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| \*\*(AC-US\d{3}-\w+)\*\* \|(.*?)\|.*\|(.*)\|\s*$", line)
        if m:
            acs[m.group(1)] = m.group(3).strip()
    return acs


def story_of(ac: str) -> str:
    return "US-" + ac.split("-")[1][2:]


def load_tcs(acs):
    data = yaml.safe_load((DOCS / "test/test-cases.yaml").read_text(encoding="utf-8"))
    scoped = [tc for tc in data["test_cases"] if set(tc.get("ac") or []) & acs.keys()]
    return data, scoped


def as_list(v):
    return v if isinstance(v, list) else [v]


# ---------------------------------------------------------------- kết quả chạy
def junit_cases(path: Path):
    """[(file, name, status)] với status ∈ passed|failed|skipped."""
    if not path.exists():
        return []
    out = []
    for tc in ET.parse(path).getroot().iter("testcase"):
        status = "passed"
        if tc.find("failure") is not None or tc.find("error") is not None:
            status = "failed"
        elif tc.find("skipped") is not None:
            status = "skipped"
        out.append((tc.get("classname", ""), tc.get("name", ""), status))
    return out


def pw_cases(path: Path):
    """[(file, title, [status của mỗi lần lặp])] từ reporter json của Playwright."""
    if not path.exists():
        return []
    out = []

    def walk(suite, file, prefix):
        file = suite.get("file", file)
        for spec in suite.get("specs", []):
            title = " ".join(p for p in [*prefix, spec["title"]] if p)
            statuses = [r["status"] for t in spec["tests"] for r in t["results"]] or ["skipped"]
            out.append((file, title, statuses))
        for child in suite.get("suites", []):
            walk(child, file, [*prefix, child["title"]] if child.get("title") != file else prefix)

    for s in json.loads(path.read_text(encoding="utf-8"))["suites"]:
        walk(s, s.get("file", ""), [])
    return out


def match_pytest(cmd: str, cases):
    """Chọn testcase junit khớp node id / -k của một lệnh pytest trong trường run."""
    args = shlex.split(cmd.split("pytest", 1)[1])
    k = args[args.index("-k") + 1] if "-k" in args else None
    nodes = [a for a in args if a.startswith("tests/")]
    picked = []
    for node in nodes:
        file, _, fn = node.partition("::")
        module = file.removesuffix(".py").replace("/", ".")
        for cls, name, st in cases:
            if not cls.endswith(module):
                continue
            base = name.split("[")[0]
            if fn and base != fn:
                continue
            if k and not any(term.strip() in base for term in k.split(" or ")):
                continue
            picked.append(st)
    return picked


def match_vitest(cmd: str, cases):
    args = shlex.split(cmd.split("vitest run", 1)[1])
    file = next(a for a in args if a.startswith("src/"))
    t = args[args.index("-t") + 1] if "-t" in args else None
    return [st for cls, name, st in cases if cls.endswith(file) and (t is None or re.search(t, name))]


def match_playwright(cmd: str, cases):
    m = re.search(r"playwright test -c \S+ (\S+\.spec\.ts)(?: -g \"([^\"]+)\")?", cmd)
    file, grep = m.group(1), m.group(2)
    out = []
    for f, title, statuses in cases:
        if f.endswith(file) and (grep is None or re.search(grep, title)):
            out.extend("passed" if s == "passed" else "failed" if s in ("failed", "timedOut") else "skipped"
                       for s in statuses)
    return out


def run_results(run_dir: Path):
    return {
        "pytest": junit_cases(run_dir / "pytest-junit.xml"),
        "vitest": junit_cases(run_dir / "vitest-junit.xml"),
        "pw": pw_cases(run_dir / "playwright/results.json"),
        "ingest": json.loads((run_dir / "ingest-fake.json").read_text(encoding="utf-8"))
        if (run_dir / "ingest-fake.json").exists() else None,
    }


def suite_summary(res) -> str:
    """Cả regression ngoài phạm vi: số pass / fail / skip của từng công cụ."""
    def count(statuses):
        f = sum(s == "failed" for s in statuses)
        k = sum(s == "skipped" for s in statuses)
        return f"{len(statuses) - f - k}✓" + (f" **{f}✗**" if f else "") + (f" {k} skip" if k else "")

    pw = ["passed" if s == "passed" else "failed" if s in ("failed", "timedOut") else "skipped"
          for _, _, st in res["pw"] for s in st]
    return " · ".join(count(x) for x in ([s for *_, s in res["pytest"]], [s for *_, s in res["vitest"]], pw))


def evidence_for(tc, run: str) -> list[tuple[str, str]]:
    """[(nhãn, đường dẫn tương đối từ docs/)] cho một TC ở một lượt."""
    ev = []
    for cmd in as_list(tc["run"]):
        if "pytest" in cmd:
            ev += [("junit", f"../reports/{run}/pytest-junit.xml"), ("log", f"../reports/{run}/pytest.log")]
        elif "vitest" in cmd:
            ev += [("junit", f"../reports/{run}/vitest-junit.xml"), ("log", f"../reports/{run}/vitest.log")]
        elif "playwright" in cmd:
            ev += [("HTML + trace + ảnh + video", f"../playwright-report/{run}/index.html"),
                   ("json", f"../reports/{run}/playwright/results.json"),
                   ("log", f"../reports/{run}/playwright.log")]
        elif "measure_ingest" in cmd:
            ev += [("json", f"../reports/{run}/ingest-fake.json"), ("log", f"../reports/{run}/ingest.log")]
    seen, out = set(), []
    for e in ev:
        if e not in seen:
            seen.add(e)
            out.append(e)
    return out


def verdict(tc, res) -> tuple[str, str]:
    """(PASS|FAIL|BLOCKED, ghi chú) theo quy tắc ở đầu test-cases.yaml."""
    layers = as_list(tc["layer"])
    if tc.get("status") == "manual" or tc.get("profile") == "REAL":
        return "BLOCKED", BLOCKED_REASON.get(layers[0], "chưa chạy")
    if res is None:
        return "BLOCKED", "chưa có lượt chạy"
    statuses = []
    for cmd in as_list(tc["run"]):
        if "measure_ingest" in cmd:
            ing = res["ingest"]
            if ing is None:
                return "BLOCKED", "thiếu ingest-fake.json"
            r = ing["runs"][0]
            ok = r.get("sequence_ok") and r.get("progress_monotonic") and r.get("final") == "ready"
            statuses.append("passed" if ok else "failed")
        elif "pytest" in cmd:
            got = match_pytest(cmd, res["pytest"])
            statuses += got or ["missing"]
        elif "vitest" in cmd:
            got = match_vitest(cmd, res["vitest"])
            statuses += got or ["missing"]
        elif "playwright" in cmd:
            got = match_playwright(cmd, res["pw"])
            if got and "repeat-each=3" in cmd and len(got) < 3:
                return "BLOCKED", f"chỉ có {len(got)} lần chạy E, cần 3"
            statuses += got or ["missing"]
    n = len(statuses)
    if "failed" in statuses:
        return "FAIL", f"{statuses.count('failed')}/{n} kết quả lỗi"
    if "missing" in statuses or "skipped" in statuses:
        return "BLOCKED", "không tìm thấy kết quả test hoặc test bị skip"
    return "PASS", f"{n}/{n} kết quả pass"


def bug_index():
    out = {}
    for f in sorted((DOCS / "bugs").glob("BUG-*.md")):
        for tc in sorted(set(re.findall(r"TC-\d{3}", f.read_text(encoding="utf-8")))):
            out.setdefault(tc, []).append(f.name)
    return out


# ---------------------------------------------------------------- viết file
def cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def code(s) -> str:
    s = str(s).replace("\n", " ").strip()
    return f"`{s}`" if "`" not in s else f"``{s}``"


def build_test_cases_md(data, acs, tcs) -> str:
    by_ac = {ac: [tc for tc in tcs if ac in tc["ac"]] for ac in acs}
    L = [
        "# Test case — US-001 và US-009 (định nghĩa PASS/FAIL)",
        "",
        "> **Sinh tự động** bằng `scripts/build_test_docs.py` từ [test/test-cases.yaml](test/test-cases.yaml) "
        "(nguồn sự thật). Không sửa tay file này.",
        f"> Định nghĩa viết ngày **{data['written']}** cho commit `{data['commit_under_test']}`, "
        "**trước** lượt chạy đầu tiên (xem lịch sử git của file YAML). File này chỉ chứa định nghĩa; "
        "kết quả chạy nằm ở [traceability.md](traceability.md).",
        "> AC đã chốt: [test/01-pham-vi-va-ac.md](test/01-pham-vi-va-ac.md). Test plan: [test-plan.md](test-plan.md).",
        "",
        "## 1. Quy tắc verdict (áp dụng cho mọi TC)",
        "",
        "| Verdict | Điều kiện |",
        "|---|---|",
        "| **PASS** | Lệnh `run` kết thúc exit code 0, **và** mọi mệnh đề trong \"PASS khi\" đúng (đã hiện thực thành assert trong mã test). Lớp E: pass **3/3** lần lặp (`--repeat-each=3`). |",
        "| **FAIL** | Bất kỳ mệnh đề nào sai, hoặc ≥ 1 lần lặp lớp E lỗi. Mọi FAIL phải có bug ticket trong [bugs/](bugs/). |",
        "| **BLOCKED** | Không đánh giá được: skip, thiếu hạ tầng (Claude thật, bge-m3), chưa có kết quả. **BLOCKED không phải PASS.** |",
        "",
        "Tính lặp lại: mỗi TC phải cho **cùng verdict ở ≥ 2 lượt chạy độc lập** (CI matrix `run-1`, `run-2`).",
        "",
        "## 2. Ma trận AC ↔ TC",
        "",
        "| User story | AC | Test case | Lớp |",
        "|---|---|---|---|",
    ]
    for ac in acs:
        ids = " · ".join(f"[{tc['id']}](#{tc['id'].lower()})" for tc in by_ac[ac])
        layers = " ".join(sorted({lay for tc in by_ac[ac] for lay in as_list(tc["layer"])}, key="UIEQP".index))
        L.append(f"| {story_of(ac)} | **{ac}** | {ids or '**THIẾU**'} | {layers} |")
    missing_ac = [ac for ac in acs if not by_ac[ac]]
    orphan = [tc["id"] for tc in tcs if not tc.get("ac")]
    L += [
        "",
        f"**Kiểm tra độ phủ (máy):** {len(acs)} AC · {len(tcs)} TC · AC không có TC: "
        f"{', '.join(missing_ac) or '**0**'} · TC không trỏ về AC: {', '.join(orphan) or '**0**'}.",
        "",
        "Ngoài phạm vi: TC-036 trở đi trong YAML thuộc các user story khác (chu kỳ 2–3) và không nằm trong file này.",
        "",
        "Lớp: " + " · ".join(f"**{k}** {v}" for k, v in LAYER_NAME.items()) + ".",
        "",
        "## 3. Chi tiết từng test case",
    ]
    for tc in tcs:
        L += [
            "",
            f"### {tc['id']}",
            "",
            f"**{cell(tc['title'])}**",
            "",
            "| | |",
            "|---|---|",
            f"| AC | {', '.join(tc['ac'])} |",
            f"| Lớp · hồ sơ | {' + '.join(as_list(tc['layer']))} · {', '.join(map(str, as_list(tc['profile'])))} |",
            f"| Mã test | {' ; '.join(code(t) for t in as_list(tc['target']))} |",
            f"| Lệnh chạy | {' ; '.join(code(r) for r in as_list(tc['run']))} |",
        ]
        if tc.get("given"):
            L.append(f"| Cho trước | {cell(tc['given'])} |")
        if tc.get("when"):
            L.append(f"| Khi | {cell(tc['when'])} |")
        if tc.get("rubric"):
            L.append(f"| Rubric | {cell(tc['rubric'])} |")
        L += ["", "**PASS khi** (tất cả đúng):", ""]
        L += [f"- {code(e)}" for e in tc["expect"]]
        L += [
            "",
            f"**Điều kiện máy đọc:** {code(tc['verdict'])}",
            "",
            "**FAIL khi:** bất kỳ mệnh đề trên sai"
            + (" ở bất kỳ lần lặp nào trong 3." if "E" in as_list(tc["layer"]) else "."),
        ]
    return "\n".join(L) + "\n", missing_ac, orphan


def build_traceability_md(acs, tcs, all_runs, results, bugs) -> tuple[str, list[str]]:
    envs = {}
    for r in all_runs:
        p = REPORTS / r / "env.txt"
        envs[r] = dict(
            line.split(": ", 1) for line in p.read_text(encoding="utf-8").splitlines() if ": " in line
        ) if p.exists() else {}
    # Verdict tính trên các lượt ở commit của lượt mới nhất; lượt ở commit cũ hơn là lịch sử (có bug ticket).
    latest = max(all_runs, key=lambda r: envs[r].get("started_utc", "")) if all_runs else None
    head = envs[latest].get("commit") if latest else None
    runs = [r for r in all_runs if envs[r].get("commit") == head]
    old_runs = [r for r in all_runs if r not in runs]

    all_verdicts = {tc["id"]: {r: verdict(tc, results[r]) for r in all_runs} for tc in tcs}
    verdicts = {t: {r: v[r] for r in runs} for t, v in all_verdicts.items()}
    final = {}
    for tc in tcs:
        vs = [verdicts[tc["id"]][r][0] for r in runs]
        if not vs:
            final[tc["id"]] = "BLOCKED"
        elif "FAIL" in vs:
            final[tc["id"]] = "FAIL"
        elif all(v == "PASS" for v in vs) and len(vs) >= 2:
            final[tc["id"]] = "PASS"
        else:
            final[tc["id"]] = "BLOCKED"
    ever_failed = {t for t, v in all_verdicts.items() if any(x == "FAIL" for x, _ in v.values())}
    fail_no_bug = sorted(t for t in ever_failed if t not in bugs)

    icon = {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "BLOCKED": "⏸ BLOCKED"}
    L = [
        "# Truy vết US ↔ AC ↔ TC ↔ bằng chứng",
        "",
        "> **Sinh tự động** bằng `scripts/build_test_docs.py` từ kết quả thật trong `reports/<lượt>/` — "
        "không sửa tay. Định nghĩa PASS/FAIL: [test-cases.md](test-cases.md).",
        "",
        "## 1. Các lượt chạy",
        "",
        "| Lượt | Bắt đầu (UTC) | Commit | File chưa commit | Hồ sơ | CI | Toàn bộ suite (pytest · vitest · Playwright ×3) "
        "| Tính verdict | Bằng chứng |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in all_runs:
        e = envs[r]
        used = "**có**" if r in runs else "không — commit cũ, xem §5"
        L.append(
            f"| {r} | {e.get('started_utc', '?')} | `{e.get('commit', '?')[:7]}` | {e.get('uncommitted_files', '?')} | "
            f"{e.get('profile', '?')} | {e.get('ci', '?')} | {suite_summary(results[r])} | {used} | "
            f"[env](../reports/{r}/env.txt) · "
            f"[exit codes](../reports/{r}/exit-codes.txt) · [Playwright](../playwright-report/{r}/index.html) · "
            f"[docker log](../reports/{r}/docker-compose.log) |"
        )
    if not all_runs:
        L.append("| — | chưa có lượt chạy nào | | | | | | |")

    if all_runs and not any(envs[r].get("ci", "").startswith("true") for r in all_runs):
        L += [
            "",
            "> **Về CI:** đã cấu hình CI ([.github/workflows/tests.yml](../.github/workflows/tests.yml)): 2 lượt độc lập "
            "trên cùng commit, lưu bằng chứng làm artifact. Lần chạy CI đầu tiên lỗi ở bước cài đặt (npm EACCES), đã sửa; "
            "từ đó GitHub Actions của tài khoản không cấp runner (các lần chạy dừng ở `queued`), nên **chưa có lần chạy CI "
            "nào hoàn tất**. Bằng chứng nộp kèm là các lượt chạy local ở trên, dùng **đúng script** "
            "[scripts/run-tests.sh](../scripts/run-tests.sh) mà CI gọi, trên code đã commit (run-4, run-5: 0 file chưa commit).",
        ]
    L += [
        "",
        "Verdict cuối của TC: **PASS** ⇔ PASS ở mọi lượt (≥ 2); **FAIL** ⇔ FAIL ở ≥ 1 lượt; còn lại **BLOCKED**. "
        "Verdict AC: PASS ⇔ mọi TC của AC đó PASS.",
        "",
        "## 2. Tổng hợp theo AC",
        "",
        "| User story | AC | TC | Verdict AC |",
        "|---|---|---|---|",
    ]
    ac_verdict = {}
    for ac in acs:
        ids = [tc["id"] for tc in tcs if ac in tc["ac"]]
        vs = [final[i] for i in ids]
        ac_verdict[ac] = "FAIL" if "FAIL" in vs else "PASS" if all(v == "PASS" for v in vs) else "BLOCKED"
        L.append(f"| {story_of(ac)} {STORIES[story_of(ac)]} | {ac} | {', '.join(ids)} | {icon[ac_verdict[ac]]} |")

    count = {v: sum(1 for x in final.values() if x == v) for v in ("PASS", "FAIL", "BLOCKED")}
    L += [
        "",
        f"**TC:** {count['PASS']} PASS · {count['FAIL']} FAIL · {count['BLOCKED']} BLOCKED / {len(tcs)}. "
        f"**AC:** {sum(v == 'PASS' for v in ac_verdict.values())} PASS / {len(acs)}.",
        "",
        "## 3. Chi tiết US ↔ AC ↔ TC ↔ bằng chứng",
        "",
        "| US | AC | TC | Lớp | " + " | ".join(f"Verdict {r}" for r in runs) + " | Ổn định | Verdict | Bằng chứng | Bug |",
        "|---|---|---|---|" + "---|" * len(runs) + "---|---|---|---|",
    ]
    for ac in acs:
        for tc in (t for t in tcs if ac in t["ac"]):
            per_run = [verdicts[tc["id"]][r] for r in runs]
            stable = "—" if len(runs) < 2 else ("có" if len({v for v, _ in per_run}) == 1 else "**không**")
            if any(v != "BLOCKED" for v, _ in per_run):
                ev = " · ".join(f"[{r}: {label}]({path})" for r in runs for label, path in evidence_for(tc, r))
            else:
                ev = per_run[0][1] if per_run else "chưa chạy"
            cells = [f"{icon[v]}<br><sub>{cell(note)}</sub>" for v, note in per_run]
            bug = ", ".join(f"[{b}](bugs/{b})" for b in bugs.get(tc["id"], [])) or (
                "**THIẾU**" if final[tc["id"]] == "FAIL" else "—")
            L.append(
                f"| {story_of(ac)} | {ac} | [{tc['id']}](test-cases.md#{tc['id'].lower()}) | "
                f"{'+'.join(as_list(tc['layer']))} | " + " | ".join(cells) +
                f" | {stable} | {icon[final[tc['id']]]} | {ev} | {bug} |"
            )
    L += [
        "",
        "## 4. TC chưa chạy được (BLOCKED) và lý do",
        "",
        "| TC | Lớp | Lý do | Cách chạy khi có điều kiện |",
        "|---|---|---|---|",
    ]
    for tc in tcs:
        if final[tc["id"]] == "BLOCKED":
            reason = verdicts[tc["id"]][runs[0]][1] if runs else "chưa có lượt chạy"
            L.append(f"| {tc['id']} | {'+'.join(as_list(tc['layer']))} | {cell(reason)} | "
                     f"{' ; '.join(code(r) for r in as_list(tc['run']))} |")
    L += [
        "",
        "## 5. Lịch sử: lượt chạy ở commit cũ",
        "",
    ]
    if not old_runs:
        L.append("Không có.")
    else:
        L += ["| Lượt | Commit | Toàn bộ suite | TC FAIL | Bug của TC | Bằng chứng |", "|---|---|---|---|---|---|"]
        for r in old_runs:
            failed = [t for t in all_verdicts if all_verdicts[t][r][0] == "FAIL"]
            tickets = sorted({b for t in failed for b in bugs.get(t, [])})
            L.append(
                f"| {r} | `{envs[r].get('commit', '?')[:7]}` | {suite_summary(results[r])} | {', '.join(failed) or '—'} | "
                f"{', '.join(f'[{b}](bugs/{b})' for b in tickets) or '—'} | "
                f"[Playwright](../playwright-report/{r}/index.html) · [log](../reports/{r}/playwright.log) |"
            )
        L += ["", "Lỗi regression ngoài phạm vi (không gắn TC) có ticket riêng: "
              + ", ".join(f"[{f.stem}](bugs/{f.name})" for f in sorted((DOCS / "bugs").glob("BUG-[0-9]*.md"))
                          if not f.name.startswith("BUG-000")) + "."]
    return "\n".join(L) + "\n", fail_no_bug


def main():
    acs = load_acs()
    data, tcs = load_tcs(acs)
    runs = sorted(p.name for p in REPORTS.glob("run-*") if p.is_dir()) if REPORTS.exists() else []
    results = {r: run_results(REPORTS / r) for r in runs}
    bugs = bug_index()

    md, missing_ac, orphan = build_test_cases_md(data, acs, tcs)
    (DOCS / "test-cases.md").write_text(md, encoding="utf-8")
    tr, fail_no_bug = build_traceability_md(acs, tcs, runs, results, bugs)
    (DOCS / "traceability.md").write_text(tr, encoding="utf-8")

    print(f"AC {len(acs)} · TC {len(tcs)} · lượt chạy {runs}")
    problems = []
    if missing_ac:
        problems.append(f"AC không có TC: {missing_ac}")
    if orphan:
        problems.append(f"TC không trỏ về AC: {orphan}")
    if fail_no_bug:
        problems.append(f"TC FAIL chưa có bug ticket: {fail_no_bug}")
    for p in problems:
        print("LỖI:", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
