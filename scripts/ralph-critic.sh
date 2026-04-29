#!/usr/bin/env bash
# ralph-critic.sh
set -euo pipefail

cat prompts/CRITIC_PROMPT.md \
  | codex exec --sandbox read-only --skip-git-repo-check - \
  | tee ".ralph/logs/critic-$(cat .ralph/iteration).log"
