# Implementation plan

## Phase 1: lexer
- [x] Implement tokenizer for parens, integers, booleans, strings, symbols (SPEC §4.1)
- [x] LexError with line/col reporting (SPEC §4.2)
- [x] Unit tests for each token class

## Phase 2: parser
- [x] Parse S-expressions into AST nodes
- [x] Handle quote sugar 'X -> (quote X)
- [x] ParseError with location
- [x] Dotted-pair / dotted-formals notation `(a . b)` for SPEC §5.4 / §5.5.5

## Phase 3: minimal evaluator
- [x] Environment class with frames
- [x] Self-evaluating literals
- [x] Symbol lookup with unbound-symbol error
- [x] Special forms: quote, if, define, lambda
- [x] Procedure application

## Phase 4: full evaluator + runtime
- [x] Special forms: set!, let, let*, letrec, cond, and, or, begin (SPEC §5.5.6–§5.5.9)
- [x] Internal defines at lambda body head (SPEC §5.5.5)
- [x] Closure / Builtin / Unspecified runtime values
- [x] Variadic and dotted lambda formals

## Phase 5: builtins (SPEC §5.1, §5.2, §5.4, §5.7, §5.8)
- [x] Arithmetic: +, -, *, /, quotient, remainder, modulo
- [x] Comparisons: <, <=, >, >=, =
- [x] Strings: string-length, string-append
- [x] Pairs/lists: cons, car, cdr, list, null?, pair?, length
- [x] Equality: eq?, equal?
- [x] I/O: display, write, newline

## Phase 6: printer (SPEC §6)
- [x] write / display modes
- [x] Proper and improper list printing
- [x] Closure / builtin / unspecified rendering

## Phase 7: CLI (SPEC §1)
- [x] File mode prints write-form per top-level expression
- [x] -e mode evaluates a single expression
- [x] REPL mode with `mylisp> ` prompt
- [x] Errors formatted as SPEC §5.9 prefixes, no Python tracebacks
- [x] Force LF line endings on Windows

## Phase 8: cleanup / outstanding
- [x] Remove tracked `=3.11...` malformed root file and `tests/unit/__pycache__` artifacts
- [x] `mylisp` shim that runs `python3 -m mylisp "$@"` (SPEC §3)
- [x] README.md content (install + one-line example, link to SPEC.md, SPEC §9.8)
- [x] examples/ programs: arithmetic, recursion, higher-order (SPEC §9.7)

## Phase 9: SPEC §9 definition-of-done audit
Gap analysis on iteration 10: every numbered SPEC §9 clause that the Builder
can satisfy is satisfied. `make all` is green (ruff clean, mypy --strict clean,
75/75 unit, 49/49 acceptance). The only outstanding clause is §9.6 (critic
must re-approve) — REVIEW.md is stale (its single complaint, missing
`examples/`, was resolved by commit 666b8e3 in iteration 9). No further
Builder work is required until the Critic re-runs `make all` and updates
REVIEW.md.
- [x] §9.1 `make all` exits 0 on a clean checkout
- [x] §9.2 acceptance coverage spans every §4 / §5 numbered subsection plus each §5.9 error prefix
- [x] §9.3 `make acceptance` reports n/n with n ≥ 40 (currently 49/49)
- [x] §9.4 `mypy --strict` clean on `src/mylisp`
- [x] §9.5 `ruff check` clean on `src` and `tests`
- [ ] §9.6 Critic's most recent REVIEW.md set to `STATUS: APPROVED` (Critic-only action)
- [x] §9.7 `examples/` has arithmetic, recursion, and higher-order programs
- [x] §9.8 README.md shows install, one-line example, and a link to SPEC.md
- [ ] §9.9 Prelude (§5.10) implemented in `src/mylisp/prelude.lisp`, loaded
  per §5.11, with acceptance coverage for every §5.10 function and the new
  error-path cases.

## Phase 10: prelude / standard library (SPEC §5.10, §5.11)

The interpreter currently exposes only the §5.1–§5.8 primitives. Phase 10
adds the §5.10 prelude. The Builder MUST follow the bootstrap order in
§5.11: builtins first, then `prelude.lisp` evaluated against the global
env, then user code. The prelude file MUST use only §5.1–§5.8 primitives
and earlier prelude definitions — no new evaluator features.

- [x] 10.1 Create `src/mylisp/prelude.lisp`. Empty or trivial content
  initially; subsequent tasks fill it in.
- [x] 10.2 Wire prelude loading in `src/mylisp/__init__.py` (or the
  environment-construction entry point used by `__main__.py`). Read the
  file via `importlib.resources` or an equivalent stdlib path lookup so
  it works under `pip install -e .`. Errors during load raise
  `RuntimeError: prelude load failed: <message>` and exit 1 (CLI),
  matching §5.10's fatal-error contract.
- [x] 10.3 Implement §5.10.1: `not`, `list?`.
- [x] 10.4 Implement §5.10.2: the 12 `c[ad]+r` selectors.
- [x] 10.5 Implement §5.10.3: `append` (variadic; preserves Scheme's
  improper-tail behavior; raises `type error:` for non-list non-tail args),
  `reverse`. Helpers are scoped inside `letrec` so the prelude exports
  only the SPEC-listed bindings (no `_append2` / `_reverse-acc` leak).
- [x] 10.6 Implement §5.10.4: `map`, `filter`, `foldl`, `foldr`. Mind the
  Racket-style `foldl` argument order (element first, accumulator second).
- [x] 10.7 Implement §5.10.5: `member`, `memq`, `assoc`, `assq`.
- [ ] 10.8 Add a `make` rule or pytest unit test that asserts the prelude
  loads cleanly on a fresh env and that each §5.10 binding is present.
- [ ] 10.9 Update `examples/` so the higher-order example (the user-land
  `map`) is rewritten or supplemented to use the prelude's `map`, `filter`,
  and `foldl` — demonstrating the prelude is the canonical entry point.

## Phase 11: `load` primitive (SPEC §5.12)

`load` is now in scope (§2 amended). It is the only mechanism for loading
external code. The Builder MUST NOT introduce search paths, dedup
tracking, or `require` semantics — those are still out of scope per the
amended §2.

Implementation order matters: 11.1 first, then tests, then 11.2–11.4
which incrementally widen the error handling.

- [x] 11.1 Implement `load` as a primitive in `src/mylisp/builtins.py`.
  Approach taken: a new `src/mylisp/loader.py` module owns a `STATE`
  singleton (global-env reference plus a source-path stack);
  `__main__._make_global_env` initialises it and `_run_file` pushes the
  resolved program path onto the stack so `load` calls inside the file
  resolve relative to its directory. The evaluator itself is unchanged.
- [x] 11.2 Implement path resolution per §5.12.1: absolute paths used
  as-is; relative paths in file mode resolve against the parent of the
  currently-evaluating source; in `-e` / REPL mode, relative paths
  resolve against `Path.cwd()`.
- [x] 11.3 Surface the error categories of §5.12.3: `type error: expected
  string, got …` for non-string args; `RuntimeError: load failed: cannot
  read …` for FileNotFoundError / IsADirectoryError / PermissionError /
  UnicodeDecodeError / generic `OSError`; `LexError` / `ParseError` now
  accept an optional `source` argument that re-renders as
  `… at line N, col M in <resolved-path>`.
- [x] 11.4 Runtime errors from forms inside the loaded file propagate
  using their existing prefixes and abort the `load`; earlier bindings
  installed in the same file are not rolled back (the `try/finally`
  only pops the source-path stack). Acceptance coverage is the Critic's
  to add per §3.
- [x] 11.4b Closure-contained relative `load`: closures now capture the
  active source path at definition time (`Closure.source`) and the
  evaluator pushes that path while applying them, so a relative `load`
  inside a closure body resolves against the directory of the file that
  defined the closure — per SPEC §5.12.1 ("the file CONTAINING the load
  call"). Regression test in `tests/unit/test_load_closure.py`.
- [ ] 11.5 Add an `examples/use_load.lisp` + `examples/helpers.lisp`
  pair showing a real `load` usage.

## Phase 12: REPL upgrades (SPEC §11)

The current REPL in `src/mylisp/__main__.py` is single-line, no history,
no directives. Phase 12 brings it up to §11.

- [ ] 12.1 Extract REPL logic from `__main__.py` into a function with the
  signature described in §11.5 (`run_repl(inputs, out, err) -> int`).
  Argparse code stays in `__main__.py` and calls `run_repl`. Unit-test
  scaffolding can drive `run_repl` with a list of strings.
- [ ] 12.2 Implement multiline accumulation (§11.1). A clean approach:
  parse the buffer after each line; on the parser's "unexpected EOF" /
  "unbalanced paren" error, keep the buffer and read another line. On
  any OTHER error, discard the buffer and report. Switch the prompt to
  `......` while the buffer is non-empty.
- [ ] 12.3 Wire `readline` per §11.2: history persistence to
  `~/.mylisp_history`, cap at 1000 entries, `ImportError` -> silent
  fallback to plain `input()`.
- [ ] 12.4 Implement directives (§11.3): `:quit`/`:q`/`:exit`, `:help`,
  `:load <path>`, `:env`. `:load` should call the same `load` machinery
  introduced in Phase 11 (do NOT duplicate the file-loading code).
  `:env` enumerates the global env's bindings — that probably requires
  exposing a `names()` method on `Environment`.
- [ ] 12.5 Error and signal recovery per §11.4: try/except around each
  evaluation, KeyboardInterrupt resets the buffer, EOF on empty prompt
  exits 0.
- [ ] 12.6 Unit tests in `tests/unit/test_repl.py` covering every clause
  enumerated in §9 clause 11 (multiline accumulation across two lines,
  each of the four directives, parse-error recovery, runtime-error
  recovery, readline-import-failure path).
