#!/usr/bin/env bash
set -euo pipefail

echo "critic" > .ralph/role
ITER=$(cat .ralph/iteration)

cat prompts/CRITIC_PROMPT.md | \
  codex exec \
    --sandbox workspace-write \
    --skip-git-repo-check \
    --cd "$(pwd)" \
    - \
  2>&1 | tee ".ralph/logs/critic-${ITER}.log"
