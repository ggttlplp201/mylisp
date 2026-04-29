#!/usr/bin/env bash
# ralph-builder.sh
set -euo pipefail

git config core.hooksPath .githooks

cat prompts/BUILDER_PROMPT.md \
  | claude --print \
          --permission-mode acceptEdits \
          --allowed-tools "Bash,Edit,Write,Read,Glob,Grep" \
          --model claude-opus-4-7 \
  | tee ".ralph/logs/builder-$(cat .ralph/iteration).log"
