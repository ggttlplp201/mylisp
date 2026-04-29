#!/usr/bin/env bash
set -euo pipefail

echo "builder" > .ralph/role
ITER=$(cat .ralph/iteration)

cat prompts/BUILDER_PROMPT.md | \
  claude --print \
         --permission-mode bypassPermissions \
         --allowed-tools "Bash,Edit,Write,Read,Glob,Grep" \
  2>&1 | tee ".ralph/logs/builder-${ITER}.log"
