# HANDOFF — mylisp

Notes for the future-you who's coming back to this project after a few
weeks or months. Read this BEFORE you touch anything.

## Status (last updated 2026-05-21)

- Branch `main` is at `0ff67f1`. Pushed to https://github.com/ggttlplp201/mylisp.
- `make all` is clean: ruff + mypy --strict + 109/109 unit + 72/72 acceptance.
- Last loop run ended on `STATUS: APPROVED` (commit `4f68ba9`).
- Spec is frozen at the level documented in `SPEC.md`: original §1–§9 plus
  §5.10 (prelude), §5.11 (bootstrap order), §5.12 (`load`), §11 (REPL).

## Where things live

- `src/mylisp/` — interpreter (lexer, parser, evaluator, builtins, prelude,
  printer, CLI). 10 files. The prelude is `src/mylisp/prelude.lisp`,
  auto-loaded at interpreter startup.
- `tests/unit/` — pytest, eight files. Driven by `make test`.
- `tests/acceptance/` — 72 `.lisp` / `.expected` pairs. Driven by
  `make acceptance`. Critic owns this directory; do not edit by hand
  unless you're fixing a portability bug the loop missed.
- `examples/` — three runnable programs: arithmetic, recursion, higher-order.
- `scripts/`, `prompts/`, `.githooks/`, `.ralph/` — the Ralph harness.

## Resume the loop

```
cd /Users/leon/mylisp
source .venv/bin/activate
make all                              # confirm green baseline
MAX_ITER=80 ./scripts/orchestrate.sh
```

If `.venv` is gone, recreate it:

```
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

System Python is 3.9 (too old; SPEC requires 3.11+). Homebrew's
`python@3.12` is the path to use. If you've moved to a different machine,
also confirm `codex` is on PATH (`/usr/local/bin/codex` here) and `claude`
is on PATH (`/Users/leon/.local/bin/claude` on the original machine, via
`.zshrc`'s `export PATH="$HOME/.local/bin:$PATH"`).

## Add a feature (the canonical motion)

1. **Amend SPEC.md** as the human role. The `.githooks/pre-commit` hook
   reads `.ralph/role`; only `human` may edit SPEC. Add a new numbered
   subsection under §5 (a primitive procedure or semantic feature) or a
   new top-level section (a new mode of operation). Be precise about
   error prefixes (§5.9), arity, types, edge cases. If the feature
   reverses a §2 non-goal (as `load` did), explicitly narrow that bullet
   rather than removing it — keeps intent traceable.

2. **Append a Phase to PLAN.md** with atomic subtasks. Aim for one commit
   per checkbox: one function family, one error category, one piece of
   plumbing.

3. **Reset REVIEW.md** to `STATUS: CHANGES_REQUESTED` with a
   `NEXT_ACTIONS_FOR_BUILDER` block pointing at the first new task.

4. **Reset `.ralph/`** if you want a clean iteration counter:

   ```
   echo 0 > .ralph/iteration
   echo builder > .ralph/lock
   echo human > .ralph/role
   : > .ralph/progress.log
   ```

5. **Commit the three files** as human, then run the orchestrator.

   ```
   git add SPEC.md PLAN.md REVIEW.md
   git commit -m "spec: ..."
   MAX_ITER=80 ./scripts/orchestrate.sh
   ```

## Operational gotchas (in order of how badly they bit)

- **codex sandbox**: `ralph-critic.sh` uses `--sandbox danger-full-access`.
  The original `workspace-write` refused `.git/index.lock` writes so the
  critic couldn't commit. Don't downgrade.
- **macOS `timeout`**: not installed by default. `orchestrate.sh` detects
  `timeout` → `gtimeout` → none. `brew install coreutils` gives `gtimeout`
  if you want the 15min/10min hard-kill safety net back.
- **`set -u` + empty bash arrays**: macOS bash 3.2 errors on `${ARR[@]}`
  when the array is empty. `orchestrate.sh` gates expansion with
  `${#ARR[@]} -gt 0` to avoid it. Don't refactor that away.
- **claude `--print` output is buffered**: the log file goes from 0 bytes
  to "everything" at end of turn. Empty `.ralph/logs/builder-N.log`
  mid-turn does NOT mean the process is hung. Check `ps aux | grep claude`
  before assuming.
- **Path-bound test fixtures**: if the critic adds a new acceptance test
  whose `.expected` file references the current checkout path
  (`/Users/leon/mylisp/...`), `make acceptance` will fail on any other
  machine. The critic SHOULD use the repo-relative form (e.g.
  `tests/acceptance/fixtures/foo.lisp`); if it doesn't, fix the
  `.expected` file by hand and tell it (via REVIEW.md) not to repeat
  the pattern.

## What's intentionally OUT of scope

These are listed in SPEC §2. Don't sneak them in:

- Macros, `define-syntax`, quasiquote
- Continuations / `call/cc`
- True tail-call optimization (Python recursion limit applies)
- A module system beyond `load` — no `require`, no search paths, no
  `MYLISP_PATH`
- Foreign function interface
- Mutable pairs (`set-car!`, `set-cdr!`)
- Floats, characters as a distinct type, vectors, hash tables, records
- `eval` of strings or s-exprs

## Ideas for future expansion (not on PLAN, not committed)

- **`apply`** — would unlock variadic `map` and is a natural §5 addition.
  Low spec surface.
- **Numeric tower** — rationals or floats. Big spec surface; rewrites §5.1.
- **`error` / condition handlers** — `(error "msg" ...)` to raise, plus
  some `with-handler` form to catch. Pairs with the existing §5.9 error
  prefixes.
- **Better REPL** — tab completion of bindings (the `:env` directive
  already enumerates them), pretty-printing of nested lists, history
  search (Ctrl-R already works via readline).
- **Module system** — would need to overturn §2 again. Decide: a real
  `require` with dedup and search paths, OR keep punting via `load`.

## When the loop gets stuck

- **STUCK at flat pass count**: likely the critic flagged a real bug but
  the builder can't fix it without spec-level guidance. Read the last
  critic log and the last few REVIEW.md verdicts. Usually the answer is
  a one-line clarification under `## Clarifications` at the bottom of
  SPEC.md.
- **STUCK with rising-then-flat count**: builder hit an ambiguity. Same
  remedy.
- **Critic reports a bug but doesn't fix it** (the iter-15 pattern): the
  critic's prompt says fix-in-turn, but it sometimes defers. Step in,
  fix the issue, leave a note in REVIEW.md so the next critic turn knows.

## When you're done for the session

- `git status` should be clean (or close to it).
- `make all` should be green.
- REVIEW.md should reflect reality — either `APPROVED` (done) or
  `CHANGES_REQUESTED` with a specific `NEXT_ACTIONS_FOR_BUILDER` block.
- Update this file's "Status" line if anything substantive moved.
