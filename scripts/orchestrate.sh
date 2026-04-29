#!/usr/bin/env bash
set -euo pipefail

MAX_ITER="${MAX_ITER:-40}"
i=0

while [ "$i" -lt "$MAX_ITER" ]; do
  i=$((i+1))
  echo "$i" > .ralph/iteration
  echo "=== iteration $i ==="

  if make acceptance >/dev/null 2>&1 && grep -q "^STATUS: APPROVED" REVIEW.md 2>/dev/null; then
    echo "DONE"; exit 0
  fi

  ./scripts/check-progress.sh || { echo "STUCK — aborting"; exit 2; }

  turn=$(cat .ralph/lock 2>/dev/null || echo "builder")
  if [ "$turn" = "builder" ]; then
    timeout 15m ./scripts/ralph-builder.sh || true
    echo "critic" > .ralph/lock
  else
    timeout 10m ./scripts/ralph-critic.sh || true
    echo "builder" > .ralph/lock
  fi
done

echo "max iterations reached"; exit 1
