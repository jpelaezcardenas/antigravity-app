#!/usr/bin/env bash
# init.sh — Harness green-gate for antigravity-app (Contexia).
#
# Run this at the START of a work session and BEFORE declaring any task `done`.
# If it fails, the session must not advance.
#
# Design note: antigravity-app is a large polyglot repo (Python backend + Next.js
# frontends). Running the FULL test suite on every Stop hook would be slow and
# flaky (needs env/DB). So this script hard-gates on CANON + HARNESS STRUCTURE and
# the one-change-at-a-time invariant, which is fast and deterministic. Full tests
# run explicitly: set RUN_TESTS=1 (backend) — the reviewer/CI runs them per change.

set -u
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; NC='\033[0m'
ok()   { printf "${GREEN}[OK]${NC}    %s\n" "$1"; }
warn() { printf "${YELLOW}[WARN]${NC}  %s\n" "$1"; }
fail() { printf "${RED}[FAIL]${NC}  %s\n" "$1"; }
EXIT_CODE=0

# Resolve a Python interpreter (python or python3)
PY=""
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
fi

echo "── 1. Living canon (must exist) ────────────────────────"
for f in ARCHITECTURE.md HARNESS.md CLAUDE.md AGENTES.md .antigravity/GROUND_TRUTH.md; do
  if [ ! -f "$f" ]; then fail "Missing canon: $f"; EXIT_CODE=1; else ok "Exists $f"; fi
done

echo ""
echo "── 2. Harness structure (must exist) ───────────────────"
for f in .claude/agents/leader.md .claude/agents/implementer.md .claude/agents/reviewer.md \
         progress/current.md progress/history.md feature_list.json \
         DEPLOYMENT_STAGE/CHECKPOINTS.md; do
  if [ ! -f "$f" ]; then fail "Missing harness file: $f"; EXIT_CODE=1; else ok "Exists $f"; fi
done

echo ""
echo "── 3. feature_list.json (one change at a time) ─────────"
if [ -z "$PY" ]; then
  warn "No python interpreter found — skipping feature_list validation"
else
  "$PY" - <<'PY'
import json, sys
try:
    data = json.load(open("feature_list.json"))
    valid = {"pending", "in_progress", "done", "blocked"}
    feats = data.get("features", [])
    in_prog = [f for f in feats if f.get("status") == "in_progress"]
    if len(in_prog) > 1:
        print(f"[FAIL]  {len(in_prog)} features in_progress (max 1)"); sys.exit(1)
    for f in feats:
        if f.get("status") not in valid:
            print(f"[FAIL]  Invalid status: {f.get('status')}"); sys.exit(1)
    print(f"[OK]    feature_list.json valid (active={data.get('active')!r}, {len(feats)} features)")
except Exception as e:
    print(f"[FAIL]  feature_list.json invalid: {e}"); sys.exit(1)
PY
  [ $? -ne 0 ] && EXIT_CODE=1
fi

echo ""
echo "── 4. Backend tests (opt-in: RUN_TESTS=1) ──────────────"
if [ "${RUN_TESTS:-0}" = "1" ] && [ -d "apps/backend" ]; then
  # Prefer whichever interpreter actually has pytest installed — on this repo's
  # dev machines, `command -v python3` can resolve to an unrelated interpreter
  # (e.g. a Windows Store alias) with no project dependencies installed, while
  # `python` is the real one. Trying both and picking the one that imports
  # pytest avoids a silent "wrong interpreter" false negative.
  PYTEST_PY=""
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c "import pytest" >/dev/null 2>&1; then
      PYTEST_PY="$candidate"
      break
    fi
  done

  if [ -z "$PYTEST_PY" ]; then
    fail "No interpreter with pytest installed found (tried python3, python)"
    EXIT_CODE=1
  else
    # Run pytest directly (not through a pipe) so its own exit code drives the
    # gate — piping through `tail` here previously made this always report
    # success, since `if pipeline; then` checks the LAST command's exit status
    # (tail's, which is always 0), not pytest's. See taty-lead-router-tenant-
    # scoping's final review report for the incident this was found in.
    pytest_output=$("$PYTEST_PY" -m pytest apps/backend -q 2>&1)
    pytest_status=$?
    echo "$pytest_output" | tail -15
    if [ $pytest_status -eq 0 ]; then
      ok "Backend tests passed"
    else
      fail "Backend tests failed (exit code $pytest_status)"
      EXIT_CODE=1
    fi
  fi
else
  warn "Skipped (set RUN_TESTS=1 to run backend tests; reviewer/CI runs them per change)"
fi

echo ""
echo "── 5. Summary ──────────────────────────────────────────"
if [ $EXIT_CODE -eq 0 ]; then ok "Harness ready. You can start working."
else fail "Harness NOT ready. Resolve the errors above before advancing."; fi
exit $EXIT_CODE
