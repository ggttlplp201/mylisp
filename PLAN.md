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
