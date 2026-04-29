#!/usr/bin/env bash
# Abort if acceptance pass count hasn't moved in 5 iterations.
set -euo pipefail

CURRENT=$(make acceptance 2>/dev/null | grep -oE 'acceptance: [0-9]+/' | grep -oE '[0-9]+')
echo "$CURRENT" >> .ralph/progress.log

# Need at least 6 entries to compare current vs 5-ago
LINES=$(wc -l < .ralph/progress.log)
if [ "$LINES" -lt 6 ]; then exit 0; fi

PAST=$(tail -6 .ralph/progress.log | head -1)
if [ "$CURRENT" -le "$PAST" ]; then
  echo "STUCK: pass count $CURRENT not improving (was $PAST 5 iters ago)"
  exit 1
fi
