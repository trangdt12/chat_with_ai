#!/usr/bin/env bash
# Chạy mọi TC chạy được ở hồ sơ FAKE (lớp U, I, E và TC-005) và gom bằng chứng của một lượt:
#   reports/<lượt>/            env.txt, exit-codes.txt, *.log, pytest-junit.xml, vitest-junit.xml,
#                              playwright/results.json, ingest-fake.json, docker-compose.log
#   playwright-report/<lượt>/  báo cáo HTML Playwright (trace, ảnh chụp, video của từng test)
# Dùng chung cho máy local và CI (.github/workflows/tests.yml). Điều kiện: `docker compose up -d` với
# LLM_FAKE=1, EMBED_FAKE=1, RETRIEVAL_NOT_FOUND_TAU=0.25; node ≥ 20 và Chromium Playwright trên host.
#
#   scripts/run-tests.sh run-1
#
# Không dừng ở bước lỗi: mọi bước đều chạy để có đủ bằng chứng; exit code ≠ 0 nếu có bước lỗi.
# Lớp Q, P (TC-006, 007, 010, 023, 028, 030) cần Claude và bge-m3 thật — không chạy ở đây.
set -uo pipefail
# Git Bash trên Windows tự đổi "/app/…" thành "C:/Program Files/Git/app/…" khi gọi docker; tắt việc đó.
export MSYS_NO_PATHCONV=1

RUN="${1:?thiếu tên lượt chạy, ví dụ: scripts/run-tests.sh run-1}"
# `pwd -W` (Git Bash trên Windows) cho dạng E:/… để node hiểu được PW_REPORT_DIR; Linux dùng pwd.
ROOT="$(cd "$(dirname "$0")/.." && (pwd -W 2>/dev/null || pwd))"
OUT="$ROOT/reports/$RUN"
PW="$ROOT/playwright-report/$RUN"
cd "$ROOT"

rm -rf "$OUT" "$PW" backend/.test-out web/.test-out
mkdir -p "$OUT"
status=0

step() {
  local name=$1; shift
  echo "== $name: $*"
  "$@" > "$OUT/$name.log" 2>&1
  local rc=$?
  echo "$name $rc" >> "$OUT/exit-codes.txt"
  echo "   exit $rc"
  [ "$rc" -eq 0 ] || status=1
}

{
  echo "run: $RUN"
  echo "started_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "commit: $(git rev-parse HEAD)"
  echo "uncommitted_files: $(git status --porcelain -- . ':!reports' ':!playwright-report' ':!.claude' | wc -l | tr -d ' ')"
  echo "ci: ${GITHUB_ACTIONS:-false} ${GITHUB_RUN_ID:+run_id=$GITHUB_RUN_ID attempt=${GITHUB_RUN_ATTEMPT:-1}}"
  echo "profile: FAKE"
  grep -E '^(LLM_FAKE|EMBED_FAKE|RETRIEVAL_NOT_FOUND_TAU)=' .env
  echo "os: $(uname -srm)"
  echo "docker: $(docker version --format '{{.Server.Version}}' 2>/dev/null)"
  echo "node: $(node --version)"
  echo "playwright: $(cd web && npx playwright --version)"
} > "$OUT/env.txt"

step ruff docker compose exec -T api ruff check .

step pytest docker compose exec -T api pytest -p no:cacheprovider -rA \
  --junitxml=/app/.test-out/pytest-junit.xml
mv backend/.test-out/pytest-junit.xml "$OUT/" 2>/dev/null

step vitest docker compose exec -T web npx vitest run --reporter=default --reporter=junit \
  --outputFile.junit=/web/.test-out/vitest-junit.xml
mv web/.test-out/vitest-junit.xml "$OUT/" 2>/dev/null
rm -rf backend/.test-out web/.test-out

step ingest docker compose exec -T api python /eval/measure_ingest.py --pages 3 --runs 1 --poll 0.2 \
  --json "/eval/reports/ingest-fake-$RUN.json"
mv "eval/reports/ingest-fake-$RUN.json" "$OUT/ingest-fake.json" 2>/dev/null

step playwright env PW_REPORT_DIR="$PW" PW_RESULTS_DIR="$OUT/playwright" \
  bash -c 'cd web && npx playwright test -c e2e/playwright.config.ts --repeat-each=3'

docker compose logs --no-color --timestamps > "$OUT/docker-compose.log" 2>&1
echo "finished_utc: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT/env.txt"

echo "Bằng chứng: reports/$RUN/, playwright-report/$RUN/"
exit $status
