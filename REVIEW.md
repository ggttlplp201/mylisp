STATUS: CHANGES_REQUESTED
ITERATION: 15
FINDINGS:
- Acceptance suite now at 61/61, unit at 100/100, ruff + mypy clean. All
  §5.10 prelude and §5.12 load acceptance coverage is in place. REPL has a
  programmatic entry point per §11.5.

RESOLVED (human, between iter 15 and resume):
- The three path-bound `err_load_*.expected` files (missing/lex/parse) were
  updated to use the repo-relative form `tests/acceptance/fixtures/...` that
  the builder's iter-6 fix produces. The .expected file is critic territory
  per SPEC §7 but iter-15 critic only reported the issue without correcting
  it; human did the byte-for-byte update to unstick the loop. Critic SHOULD
  treat hardcoded-absolute-path expectations as something it fixes
  immediately on detection going forward, not something it defers.

NEXT_ACTIONS_FOR_BUILDER:
- Resume PLAN.md work: 10.8 (prelude binding presence unit test), 10.9
  (rewrite `examples/higher_order.lisp` to use prelude's `map`/`filter`/`foldl`),
  11.5 (`examples/use_load.lisp` + `examples/helpers.lisp`).
- Phase 12 REPL is partly implemented (commit `5aa3779`). Audit what's
  actually done versus the §11 requirements (multiline accumulation,
  readline history, all four directives, error/signal recovery) and
  finish whatever's missing. Verify §9.11 unit-test coverage.

NEXT_ACTIONS_FOR_CRITIC:
- When you find a hardcoded-input test, FIX it in the same turn — do not
  just report it. tests/acceptance/ is critic territory; that's why
  CRITIC_PROMPT.md step 5 says "If acceptance tests are missing for any
  SPEC requirement, ADD them." The same applies to broken ones.
