#!/usr/bin/env bash
set -euo pipefail

MAX_ITER="${MAX_ITER:-40}"
i=0

# macOS has no `timeout` by default; `gtimeout` ships with coreutils.
# Detect once; if neither is present, run unbounded (the agents normally
# finish in a few minutes anyway).
if command -v timeout >/dev/null 2>&1; then
  TIMEOUT_CMD=(timeout)
elif command -v gtimeout >/dev/null 2>&1; then
  TIMEOUT_CMD=(gtimeout)
else
  TIMEOUT_CMD=()
fi

run_with_timeout() {
  local dur="$1"; shift
  if [ "${#TIMEOUT_CMD[@]}" -gt 0 ]; then
    "${TIMEOUT_CMD[@]}" "$dur" "$@"
  else
    "$@"
  fi
}

while [ "$i" -lt "$MAX_ITER" ]; do
  i=$((i+1))
  echo "$i" > .ralph/iteration
  echo "=== iteration $i ==="

  if make acceptance >/dev/null 2>&1 && grep -q "^STATUS: APPROVED" REVIEW.md 2>/dev/null; then
    echo "DONE"; exit 0
  fi

  if [ "$i" -gt 6 ]; then
    ./scripts/check-progress.sh || { echo "STUCK — aborting"; exit 2; }
  fi

  turn=$(cat .ralph/lock 2>/dev/null || echo "builder")
  if [ "$turn" = "builder" ]; then
    run_with_timeout 15m ./scripts/ralph-builder.sh || true
    echo "critic" > .ralph/lock
  else
    run_with_timeout 10m ./scripts/ralph-critic.sh || true
    echo "builder" > .ralph/lock
  fi
done

echo "max iterations reached"; exit 1
