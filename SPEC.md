# SPEC: `mylisp` — A Scheme-flavored Lisp Interpreter

**Status:** frozen. This file is the contract. The Builder agent MUST NOT modify it.
The Critic agent MAY append clarifications under `## Clarifications` only — never edit existing requirements.

---

## 1. Goal

Build a tree-walking interpreter for a small Scheme-flavored Lisp, called `mylisp`,
implemented in Python 3.11+ with no third-party runtime dependencies (stdlib only).

The interpreter must:

1. Run as `./mylisp <file.lisp>` and execute the file, printing the value of each
   top-level expression to stdout, one per line, in the format defined in §6.
2. Run as `./mylisp` (no args) and start a REPL.
3. Run as `./mylisp -e "<expr>"` and print the result of evaluating `<expr>`.
4. Pass every program in `tests/acceptance/` with output matching the corresponding
   `.expected` file byte-for-byte.

Anything not specified in this document is out of scope. If a feature is not in
§4 or §5, it must not be implemented. Adding scope is a SPEC violation.

---

## 2. Non-goals

These are explicitly excluded. Implementing them is a SPEC violation:

- Macros (`define-syntax`, `syntax-rules`, `defmacro`, quasiquotation beyond §5.6).
- Continuations / `call/cc`.
- Tail-call optimization beyond what Python's recursion limit naturally allows.
  The reference test suite never recurses deeper than 200 frames.
- A module / `import` / `require` system.
- A foreign function interface.
- Mutable pairs (`set-car!`, `set-cdr!`). Pairs are immutable.
- Floating-point. All numbers are Python `int`. See §5.1.
- Strings as anything other than opaque immutable values. No `string-ref`,
  `substring`, etc. — see §5.2 for the full string API.
- Characters as a distinct type. There is no `#\a` syntax.
- Vectors, hash tables, records.
- File I/O beyond reading the program file at startup.
- Any form of `eval` exposed to user code.

---

## 3. Project layout

The agents must produce and maintain exactly this layout:

```
.
├── SPEC.md                     (this file, immutable)
├── AGENTS.md                   (build/test commands, conventions)
├── PLAN.md                     (task list)
├── REVIEW.md                   (critic verdict)
├── README.md                   (user-facing; one short example)
├── Makefile                    (targets defined in §8)
├── mylisp                      (executable shim; runs `python3 -m mylisp "$@"`)
├── pyproject.toml              (no runtime deps; dev deps: pytest, ruff, mypy)
├── src/
│   └── mylisp/
│       ├── __init__.py
│       ├── __main__.py         (CLI entry; arg parsing only)
│       ├── lexer.py
│       ├── parser.py
│       ├── ast.py              (data classes for AST nodes)
│       ├── env.py              (Environment class)
│       ├── builtins.py         (primitive procedures)
│       ├── evaluator.py        (eval/apply)
│       └── printer.py          (value -> string, see §6)
├── tests/
│   ├── unit/                   (Builder writes these)
│   └── acceptance/             (Critic writes these; see §7)
└── examples/                   (user-readable demo programs)
```

The Builder MUST NOT create files outside `src/`, `tests/unit/`, `examples/`,
`README.md`, `PLAN.md`, `Makefile`, or `pyproject.toml`.
The Critic MUST NOT create files outside `tests/acceptance/`, `REVIEW.md`,
or appendices to this SPEC.

---

## 4. Lexical syntax

A program is a sequence of S-expressions separated by whitespace.

### 4.1 Tokens

- **Whitespace:** space, tab, newline, carriage return. Significant only as
  a separator.
- **Comments:** `;` to end-of-line. Discarded.
- **Parens:** `(` and `)`.
- **Quote:** `'` is shorthand: `'X` reads as `(quote X)`.
- **Integer:** optional `-`, then one or more decimal digits. Examples: `0`,
  `42`, `-7`. `+3` is NOT a valid integer (it is a symbol).
- **Boolean:** `#t` and `#f`. No other `#`-prefixed tokens are valid.
- **String:** `"..."`. Supports escapes `\\`, `\"`, `\n`, `\t`. No other
  escapes are valid; `\x` is a lex error.
- **Symbol:** any sequence of characters from the set
  `[a-zA-Z+\-*/<>=!?_]` followed by zero or more of
  `[a-zA-Z0-9+\-*/<>=!?_]`. Symbols are case-sensitive. `+`, `-`, `*`, `/`,
  `<`, `>`, `=`, `<=`, `>=` are valid symbols.

### 4.2 Errors

Lex errors must be reported as `LexError: <message> at line <n>, col <m>`
to stderr, with exit code 1. Line and column are 1-based.

---

## 5. Semantics

### 5.1 Numbers

The only numeric type is integer (Python `int`, arbitrary precision).

Arithmetic primitives: `+`, `-`, `*`, `/`, `modulo`, `quotient`, `remainder`.

- `+` and `*` take zero or more args. `(+ )` => `0`. `(* )` => `1`.
- `-` with one arg negates. With two or more, left-fold subtraction.
  `(- )` is an arity error.
- `/` is **integer division, truncating toward zero**. `(/ 7 2)` => `3`.
  `(/ -7 2)` => `-3`. Division by zero raises `RuntimeError: division by zero`.
- `quotient` and `remainder` follow R7RS truncated semantics.
  `modulo` follows R7RS floored semantics.
- Comparisons: `<`, `<=`, `>`, `>=`, `=`. All take exactly two integer args.
  Return `#t` or `#f`.

### 5.2 Strings

Strings are immutable. The only operations are:

- Reading them as literals (§4.1).
- Comparing with `equal?`.
- Printing them. `display` prints without quotes; `write` prints with quotes
  and escaped contents.
- `string-length` returns the character count as an integer.
- `string-append` concatenates zero or more strings.

### 5.3 Booleans and truthiness

Only `#f` is false. Every other value, including `0`, `'()`, and `""`,
is true. This matches Scheme; do not import Python truthiness.

### 5.4 Pairs and lists

`(cons a b)` builds a pair. `(car p)` and `(cdr p)` access its halves.

A **list** is either the empty list `'()` or a pair whose `cdr` is a list.
Lists print using list notation: `(1 2 3)`, not `(1 . (2 . (3 . ())))`.
Improper pairs print with a dot: `(1 . 2)`.

Required list primitives: `cons`, `car`, `cdr`, `list`, `null?`, `pair?`,
`length` (error on improper list).

### 5.5 Special forms

These are NOT procedures. They have non-standard evaluation rules. The Builder
must handle them in the evaluator, not as builtins.

#### 5.5.1 `quote`

`(quote X)` returns `X` unevaluated. `'X` is reader sugar for `(quote X)`.

#### 5.5.2 `if`

`(if cond then else)` — `else` is required (no one-armed `if`). Only
the selected branch is evaluated.

#### 5.5.3 `define`

Two forms:

- `(define <symbol> <expr>)` — evaluates `<expr>` in the current env and
  binds the result to `<symbol>` in the current env.
- `(define (<name> <param>...) <body>...)` — sugar for
  `(define <name> (lambda (<param>...) <body>...))`.

`define` at the top level adds to the global env. Inside a `lambda` body,
`define` is permitted only at the head of the body and adds to the local
frame. `define` returns an unspecified value; printing it is implementation-
defined but the REPL must NOT print anything for a top-level `define`.

#### 5.5.4 `set!`

`(set! <symbol> <expr>)` — mutates an existing binding. Errors if `<symbol>`
is not bound. Returns unspecified; the REPL must not print a result.

#### 5.5.5 `lambda`

`(lambda (<param>...) <body>...)` — creates a closure capturing the current
env. The body is one or more expressions; the value of the last is returned.
Internal `define`s (see §5.5.3) come first.

Variadic forms:

- `(lambda <symbol> <body>...)` binds all args as a list to `<symbol>`.
- `(lambda (<p1> <p2> . <rest>) <body>...)` binds the first two args
  positionally and any remainder as a list to `<rest>`.

#### 5.5.6 `let`, `let*`, `letrec`

- `(let ((<v1> <e1>) ...) <body>...)` — evaluates all `<ei>` in the enclosing
  env, then binds and runs the body.
- `(let* ...)` — left-to-right, each binding sees the previous.
- `(letrec ...)` — all bindings are introduced (initially unspecified) before
  any `<ei>` is evaluated; suitable for mutually recursive `lambda`s.

Named `let` (`(let loop ((x 0)) ...)`) is OUT OF SCOPE.

#### 5.5.7 `cond`

`(cond (<test> <expr>...) ... (else <expr>...))`. The first clause whose
test is not `#f` has its body evaluated; the value of the last expr is
returned. `else` is required if no clause is guaranteed to match;
falling off the end returns an unspecified value (the printer must emit
nothing for it at the REPL). The `=>` form is OUT OF SCOPE.

#### 5.5.8 `and`, `or`

Short-circuiting. `(and)` => `#t`. `(or)` => `#f`. `and` returns the last
value if all are truthy; `or` returns the first truthy value. Both must
short-circuit (later args are not evaluated).

#### 5.5.9 `begin`

`(begin <expr>...)` evaluates each in order and returns the value of the
last. `(begin)` is an arity error.

### 5.6 Quote only

`quote` is the only quotation form. `quasiquote` / `unquote` / `unquote-splicing`
(`` ` `` `,` `,@`) are OUT OF SCOPE.

### 5.7 Equality

- `eq?` — identity for pairs, closures, symbols. Equality for booleans and
  the empty list. For integers within the small-int range Python interns,
  the result is implementation-defined; tests must not depend on `eq?` of
  numbers or strings.
- `equal?` — structural equality. Recurses into pairs. For numbers, strings,
  booleans, symbols, the empty list: value equality.
- `=` — numeric equality, two args, both must be integers.

### 5.8 I/O

- `(display <v>)` — prints `<v>` using display form (§6), no trailing newline.
- `(newline)` — prints a single newline.
- `(write <v>)` — prints `<v>` using write form (§6), no trailing newline.

These are the only I/O procedures. Reading is out of scope.

### 5.9 Errors at runtime

Runtime errors are reported as `RuntimeError: <message>` to stderr, exit
code 1. The interpreter must not print a Python traceback to the user.
A REPL must catch the error, print the message, and continue.

Required error categories (the message MUST start with the listed prefix):

- `unbound symbol: <name>`
- `not a procedure: <printed value>`
- `arity mismatch: expected <n>, got <m>` (or `expected at least <n>, got <m>`
  for variadic)
- `type error: expected <type>, got <printed value>`
- `division by zero`

---

## 6. Printing

Two modes: **display** and **write**. Top-level results in file mode and the
REPL use **write** mode.

| Value             | display       | write              |
|-------------------|---------------|--------------------|
| Integer `42`      | `42`          | `42`               |
| `#t` / `#f`       | `#t` / `#f`   | `#t` / `#f`        |
| Empty list        | `()`          | `()`               |
| Symbol `foo`      | `foo`         | `foo`              |
| String `"hi\n"`   | `hi<newline>` | `"hi\n"`           |
| Pair `(1 2 3)`    | `(1 2 3)`     | `(1 2 3)`          |
| Improper `(1 . 2)`| `(1 . 2)`     | `(1 . 2)`          |
| Closure           | `#<procedure>`| `#<procedure>`     |
| Builtin `+`       | `#<builtin +>`| `#<builtin +>`     |
| Unspecified       | (no output)   | (no output)        |

In file mode, the value of every top-level expression is printed in **write**
form followed by a single `\n`, EXCEPT for `define` and `set!` which print
nothing. In REPL mode, identical rules apply; the prompt is `mylisp> ` and
errors do not exit.

Trailing whitespace at end of output is forbidden. The final line ends with
`\n`. No BOM.

---

## 7. Acceptance tests

The Critic owns `tests/acceptance/`. Each test is two files:

```
tests/acceptance/<name>.lisp
tests/acceptance/<name>.expected
```

The test runner (`make acceptance`) runs `./mylisp <name>.lisp` and compares
stdout to `<name>.expected` byte-for-byte. A test passes iff:

1. Exit code is 0 (or the test name starts with `err_`, in which case exit
   code must be 1 and stderr is compared to `<name>.expected` instead).
2. Output matches exactly.

The Critic must, at minimum, write acceptance tests covering every numbered
subsection of §4 and §5, plus error-path tests for each error category in §5.9.

The Critic MUST NOT weaken a test once written. Adding new tests is allowed;
deleting or relaxing existing ones is a SPEC violation. Tests can only be
edited to fix a typo in `.expected` against an unambiguous SPEC reading;
such edits require a note in `REVIEW.md`.

---

## 8. Build, test, lint targets

The Builder must keep these `make` targets working from iteration 1 onward.
`make` with no target runs `make all`.

| Target           | Behavior                                                 |
|------------------|----------------------------------------------------------|
| `make all`       | Equivalent to `make lint typecheck test acceptance`.     |
| `make test`      | `pytest tests/unit -q`. Exit 0 iff all pass.             |
| `make acceptance`| Runs every `tests/acceptance/*.lisp`. Exit 0 iff all pass.|
| `make lint`      | `ruff check src tests`. Exit 0 iff clean.                |
| `make typecheck` | `mypy --strict src/mylisp`. Exit 0 iff clean.            |
| `make repl`      | `./mylisp`. For human use; not run in CI.                |
| `make clean`     | Removes `__pycache__`, `.pytest_cache`, `.mypy_cache`.   |

`make acceptance` must print, on stdout, a final line of the form
`acceptance: <pass>/<total> passed` and exit non-zero if pass < total.
The Ralph progress checker depends on this exact format.

---

## 9. Definition of done

The project is DONE when ALL of the following hold simultaneously:

1. `make all` exits 0 on a clean checkout (after `pip install -e .[dev]`).
2. `tests/acceptance/` contains at least one test for every numbered
   subsection of §4 and §5, and at least one error-path test for each
   prefix in §5.9.
3. `make acceptance` reports `<n>/<n> passed` with `n >= 40`.
4. `mypy --strict` is clean on `src/mylisp`.
5. `ruff check` is clean on `src` and `tests`.
6. The Critic's most recent `REVIEW.md` has `STATUS: APPROVED`.
7. `examples/` contains at least three runnable example programs:
   one arithmetic, one recursion, one higher-order (e.g. `map` defined
   in user code).
8. `README.md` shows installation, a one-line example, and a link to
   `SPEC.md`.

The Builder MUST NOT mark the project done by any other criterion. The
Critic MUST verify each clause of §9 independently before approving.

---

## 10. Process rules (binding on both agents)

1. One focused commit per turn. Conventional commit prefix: `feat:`, `fix:`,
   `test:`, `refactor:`, `docs:`, `chore:`.
2. Never delete or weaken a test in `tests/acceptance/` to make a build pass.
   Doing so is grounds for the orchestrator to abort the run.
3. Never widen scope past §4–§5. If a feature seems necessary and is not
   listed, append a `BLOCKED:` entry to `PLAN.md` and exit. The human
   resolves it by editing this SPEC.
4. If you are about to write code that "feels like" macros, continuations,
   or eval-of-user-code, stop. Those are out of scope (§2).
5. The Builder reads `REVIEW.md` first every turn and addresses the top
   `CHANGES_REQUESTED` item before picking new work.
6. The Critic runs the full `make all` every turn before writing `REVIEW.md`.

---

## Clarifications

(Empty. Critic appends here only, with date and brief rationale, when SPEC
language proves genuinely ambiguous in practice.)
x  
 