STATUS: CHANGES_REQUESTED
ITERATION: 10
FINDINGS:
- SPEC.md amended by the human role. New material:
  * §2 (Non-goals) — narrowed bans on file I/O, modules, and eval to permit
    `load` while keeping `require`, search paths, and `eval`-of-strings out
    of scope.
  * §5.10 + §5.11 — Prelude (standard library) and bootstrap order.
  * §5.12 — `load` primitive with calling-file-relative path resolution.
  * §10 process rule #3 updated to mention §11.
  * §11 — REPL behavior (multiline input, readline history, directives,
    programmatic entry point for tests).
  * §9 — new clauses 9, 10, 11 covering prelude, load, and REPL.
- `src/mylisp/prelude.lisp` does not exist.
- `load` not implemented.
- REPL still single-line, no directives, no history.
- No acceptance tests cover §5.10, §5.12, or §11.
NEXT_ACTIONS_FOR_BUILDER:
- Work through PLAN.md in phase order: Phase 10 (prelude) MUST finish
  before Phase 11 (load) starts, and Phase 11 MUST finish before Phase 12
  (REPL), because Phase 12's `:load` directive uses the Phase 11 primitive.
- Start with tasks 10.1 and 10.2 as previously instructed: create
  `src/mylisp/prelude.lisp` and wire host-side loading. Do not implement
  §5.10.3 onward, §5.12, or §11 yet — each subtask is its own commit.
