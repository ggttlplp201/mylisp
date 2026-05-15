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
- A module system with search paths, dedup tracking, or namespaces.
  `require`, `provide`, `import`, and `MYLISP_PATH`-style env-var resolution
  are all out of scope. The `load` primitive of §5.12 is the ONLY mechanism
  for loading external code.
- A foreign function interface.
- Mutable pairs (`set-car!`, `set-cdr!`). Pairs are immutable.
- Floating-point. All numbers are Python `int`. See §5.1.
- Strings as anything other than opaque immutable values. No `string-ref`,
  `substring`, etc. — see §5.2 for the full string API.
- Characters as a distinct type. There is no `#\a` syntax.
- Vectors, hash tables, records.
- User-level file I/O beyond the `load` primitive of §5.12. No
  `read-file`, `write-file`, `open`, port objects, or any user-visible way
  to interact with the filesystem outside of `load`.
- `eval` of strings or in-memory s-expressions exposed to user code.
  `load` (§5.12) reads, parses, and evaluates a file's top-level forms;
  it is NOT an `eval` primitive over arbitrary data.

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
│       ├── printer.py          (value -> string, see §6)
│       └── prelude.lisp        (Lisp-defined standard library, §5.10)
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

### 5.10 Prelude (standard library)

A set of Lisp-defined functions that the interpreter MUST make available
in the global environment of every program before user code runs.

**Delivery.** The prelude is the file `src/mylisp/prelude.lisp`. At
interpreter startup, after the global environment is populated with the
builtins of §5.1–§5.8 and before any user program, `-e` expression, or REPL
input is evaluated, the interpreter MUST load and evaluate every top-level
form in `prelude.lisp` against the global env. The prelude file is read by
the host (Python) and is NOT user-visible file I/O — §2's ban on file I/O
still applies to user code. Any error raised while loading the prelude is
fatal: the interpreter prints `RuntimeError: prelude load failed: <message>`
to stderr and exits with code 1.

**Visibility.** Prelude bindings live in the same global frame as builtins.
User code may shadow them with `define` or mutate them with `set!`. The
interpreter MUST NOT expose any way for user code to re-load, skip, or
introspect the prelude.

**Implementation constraints.**

- `prelude.lisp` may use ONLY the primitives of §5.1–§5.8 and earlier
  prelude definitions. No new evaluator features.
- Every function below MUST be defined in `prelude.lisp`, not as a Python
  builtin. Defining any §5.10 function in Python is a SPEC violation.
- Type errors propagate naturally from the underlying `car`/`cdr`/etc.
  calls and use the existing §5.9 prefixes. The prelude introduces no new
  error categories.

#### 5.10.1 Predicates

- `(not x)` — returns `#t` if `x` is `#f`, else `#f`. Arity 1.
- `(list? x)` — returns `#t` if `x` is `'()` or a pair whose `cdr` is itself
  a list (recursive definition). Returns `#f` for any other value, including
  improper pairs such as `(cons 1 2)`. Arity 1.

#### 5.10.2 Pair selectors

The following 12 functions, each a composition of `car`/`cdr` read
right-to-left (so `(cadr p)` is `(car (cdr p))`):

```
caar  cadr  cdar  cddr
caaar caadr cadar caddr
cdaar cdadr cddar cdddr
```

Each takes one argument. Errors propagate from `car`/`cdr` when the input
is not a pair at the required depth.

#### 5.10.3 List construction

- `(append . lsts)` — variadic. Returns the concatenation of its arguments.
  `(append)` returns `'()`. `(append lst)` returns `lst`. With two or more
  args, every argument except the last must be a proper list; if a non-last
  argument is not a proper list, raise a `type error:` (§5.9). The last
  argument may be any value and becomes the tail of the result (matching
  Scheme: `(append '(1 2) 3)` => `(1 2 . 3)`).
- `(reverse lst)` — returns a new proper list with the elements of `lst`
  in reverse order. `lst` MUST be a proper list; otherwise `type error:`.

#### 5.10.4 Higher-order list operations

- `(map f lst)` — applies `f` to each element of `lst` in order and returns
  a proper list of the results. Arity 2. Multi-list `map` is OUT OF SCOPE
  (the interpreter has no `apply` primitive). `lst` MUST be a proper list.
- `(filter pred lst)` — returns a new proper list containing those elements
  `x` of `lst` for which `(pred x)` is not `#f`, in original order. Arity 2.
- `(foldl f init lst)` — left fold. For `lst = (a b c)`:
  `(foldl f init '(a b c))` = `(f c (f b (f a init)))`. That is, `f`
  receives the current element first and the accumulator second (Racket
  convention). Arity 3.
- `(foldr f init lst)` — right fold. For `lst = (a b c)`:
  `(foldr f init '(a b c))` = `(f a (f b (f c init)))`. Arity 3.

For all four, `lst` MUST be a proper list.

#### 5.10.5 List search

- `(member x lst)` — returns the first sublist of `lst` whose `car` is
  `equal?` to `x`, or `#f` if no such sublist exists. Arity 2.
- `(memq x lst)` — same, but using `eq?`. Arity 2.
- `(assoc k alst)` — `alst` is an association list (a list of pairs).
  Returns the first pair in `alst` whose `car` is `equal?` to `k`, or `#f`
  if no such pair exists. Arity 2.
- `(assq k alst)` — same, but using `eq?`. Arity 2.

For all four, the list argument MUST be a proper list. For `assoc`/`assq`,
encountering a non-pair element while searching raises a `type error:`.

### 5.11 Prelude bootstrap order

Builtins (§5.1–§5.8) MUST be installed in the global env before
`prelude.lisp` is loaded. The prelude MUST be fully evaluated before any
of the following happens:

1. A user file (file mode) is read.
2. A `-e` expression is parsed.
3. The first REPL prompt is shown.

REPL sessions load the prelude exactly once, at startup. Successive
inputs share the same global env (and thus the same prelude bindings).

### 5.12 `load`

`(load <path>)` reads, parses, and evaluates the file at `<path>` against
the global environment. Returns an unspecified value (the REPL prints
nothing for it, and `load` at the top level of a file produces no output).
Arity 1; `<path>` MUST be a string.

`load` is a primitive procedure, not a special form. Its argument is
evaluated before the call (so `(load (string-append dir "/foo.lisp"))`
works once a `string-append`-returning expression is available).

#### 5.12.1 Path resolution

- If `<path>` begins with `/`, it is absolute and used as-is.
- Otherwise it is relative:
  - In file mode, `<path>` is resolved relative to the directory of the
    file CONTAINING the `load` call. Recursive loads are each resolved
    against the directory of the file that issued them. The CLI's initial
    program file is treated as if loaded from the current working
    directory, so a top-level `(load "x.lisp")` in `./main.lisp` invoked
    as `./mylisp ./main.lisp` looks for `./x.lisp` (i.e. the directory
    of `main.lisp` after resolving the initial file's path).
  - In `-e` mode, `<path>` is resolved relative to the current working
    directory.
  - In REPL mode, `<path>` is resolved relative to the current working
    directory at the time the call is evaluated.
- The interpreter MUST NOT consult any environment variable, configuration
  file, or built-in search path. There is no `MYLISP_PATH`.

#### 5.12.2 Evaluation semantics

The target file is read as bytes, decoded as UTF-8, and parsed as a
sequence of top-level S-expressions (§4). Each form is evaluated in order
against the GLOBAL environment, regardless of where the `load` call
appears lexically. `define` adds bindings to the global env; `set!`
mutates existing bindings.

Top-level values produced during `load` are NOT printed — `load` is
silent on success, unlike file mode at the CLI which prints each
top-level value per §6.

`load` does NOT track previously-loaded files. Calling `load` twice with
the same resolved path evaluates the file twice; side effects compound.
Cycles in `load` chains (a.lisp loads b.lisp loads a.lisp) are not
detected. If the chain is infinite, the host's recursion limit applies
and the resulting error surfaces per §5.9.

#### 5.12.3 Errors

All `load` errors surface using §5.9 prefixes:

- `type error: expected string, got <printed value>` — non-string `<path>`.
- `RuntimeError: load failed: cannot read <resolved-path>: <reason>` —
  file does not exist, is unreadable, is a directory, or fails UTF-8
  decoding. `<reason>` is a short host-supplied phrase, not a Python
  traceback.
- `LexError: <message> at line <n>, col <m> in <resolved-path>` — `<resolved-path>`
  replaces the implicit `<stdin>` source in the location string.
- `ParseError: <message> at line <n>, col <m> in <resolved-path>` —
  same treatment.
- Runtime errors from forms inside the loaded file propagate normally,
  using their existing prefixes, and ABORT the `load`. Bindings already
  installed by earlier forms in the same file are NOT rolled back.

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
9. `src/mylisp/prelude.lisp` exists, is loaded at interpreter startup per
   §5.10–§5.11, and `tests/acceptance/` contains at least one passing test
   exercising each function listed in §5.10.1 through §5.10.5 (including
   each of the 12 `c[ad]+r` selectors), plus at least one error-path test
   covering the new `type error:` cases introduced by `append`, `reverse`,
   `assoc`, and `assq`.
10. `load` (§5.12) is implemented as a primitive. `tests/acceptance/`
    contains at least one happy-path test (a file that uses `load` to pull
    in a helper file and observes a binding it defined), and at least one
    error-path test for each new error category in §5.12.3
    (non-string path, missing file, lex/parse error in the loaded file,
    runtime error in the loaded file).
11. REPL upgrades (§11) are implemented and exercised. Because REPL
    sessions are interactive and not directly executable from `make
    acceptance`, the Builder MUST add UNIT tests in `tests/unit/` that
    drive the REPL via its programmatic entry point (a function callable
    with a `Iterable[str]` of input lines and an output stream). The
    tests MUST cover: multiline accumulation across two lines, each
    of `:quit`/`:help`/`:load`/`:env`, recovery after a parse error,
    recovery after a runtime error, and graceful degradation when
    `readline` import fails.

The Builder MUST NOT mark the project done by any other criterion. The
Critic MUST verify each clause of §9 independently before approving.

---

## 10. Process rules (binding on both agents)

1. One focused commit per turn. Conventional commit prefix: `feat:`, `fix:`,
   `test:`, `refactor:`, `docs:`, `chore:`.
2. Never delete or weaken a test in `tests/acceptance/` to make a build pass.
   Doing so is grounds for the orchestrator to abort the run.
3. Never widen scope past §4, §5, or §11. If a feature seems necessary and
   is not listed, append a `BLOCKED:` entry to `PLAN.md` and exit. The
   human resolves it by editing this SPEC.
4. If you are about to write code that "feels like" macros, continuations,
   or eval-of-user-code, stop. Those are out of scope (§2).
5. The Builder reads `REVIEW.md` first every turn and addresses the top
   `CHANGES_REQUESTED` item before picking new work.
6. The Critic runs the full `make all` every turn before writing `REVIEW.md`.

---

## 11. REPL behavior

The REPL is the no-args mode (`./mylisp`). Beyond the basic prompt-and-eval
loop described in §1 and §6, the REPL MUST support the following:

### 11.1 Multiline input

The REPL reads input one line at a time. If the accumulated buffer is not
yet a complete sequence of one or more S-expressions — because parens are
unbalanced, a quoted form is missing its target, or a string literal is
unterminated — the prompt MUST switch from `mylisp> ` to `...... ` (six
characters, matching the column width of the primary prompt) and the REPL
MUST keep reading until the buffer parses cleanly. The completed
expressions are then evaluated and printed per §6 in submission order.

A single line containing multiple complete S-expressions is treated as
multiple top-level expressions, each evaluated and printed in order.

The accumulated buffer is discarded on any of: EOF, KeyboardInterrupt
(Ctrl-C), a LexError, a ParseError, or a RuntimeError. After such an
event the REPL returns to the `mylisp> ` prompt with an empty buffer.

### 11.2 Command history

The REPL MUST integrate with Python's stdlib `readline` (no third-party
deps). Up/down arrow keys recall prior submissions; left/right arrows and
the standard line-editing bindings work.

History MUST persist between sessions in `~/.mylisp_history`. The file is
created on first session if absent. Each entry is one submitted line
(multiline submissions become multiple readline entries — that is the
behavior `readline.write_history_file` produces and is acceptable). The
history file is capped at 1000 entries; older entries are dropped.

The REPL MUST tolerate the absence of the `readline` module (some Windows
Pythons ship without it) by catching `ImportError` at startup and
silently degrading to plain `input()`. No warning, no error.

### 11.3 Directives

Any submission whose first non-whitespace character is `:` (colon) is a
REPL directive, NOT an expression to evaluate. The directive name is the
first whitespace-delimited token after the colon; arguments follow.
Unknown directives print

```
REPL: unknown directive :<name>. Try :help.
```

to stderr and the REPL continues.

Directives MUST NOT be available outside the REPL. File mode and `-e`
mode treat a leading `:` per §4.1: `:` is not in the symbol charset and
will surface as a `LexError`.

The following directives MUST be supported:

- `:quit` (aliases: `:q`, `:exit`) — exits the REPL with status 0.
  Ctrl-D on an empty `mylisp> ` prompt has the same effect.
- `:help` — prints a fixed help block listing every directive on a
  separate line with a short description. The exact text is the
  Builder's choice; the Critic's acceptance is that every directive name
  in this section appears in the output.
- `:load <path>` — equivalent to evaluating `(load "<path>")` at the
  prompt. `<path>` is the rest of the submission after `:load` and one
  whitespace character, trimmed of trailing whitespace. The path is NOT
  quoted in the source; `:load foo bar.lisp` passes the literal string
  `foo bar.lisp`. Errors are reported per §5.9 and the REPL continues.
- `:env` — prints the names of every binding currently visible in the
  global environment, ONE NAME PER LINE, in C-locale (byte-wise) sorted
  order. Builtins (§5.1–§5.8) and prelude bindings (§5.10) are included.
  No values are printed. The output ends with a single trailing newline.

### 11.4 Error and signal recovery

A LexError, ParseError, or RuntimeError raised during a REPL submission
MUST be caught, formatted per §5.9 (LexError uses §4.2 format), printed
to stderr, and the REPL MUST return to the `mylisp> ` prompt with an
empty buffer. Python tracebacks MUST NOT reach the user.

KeyboardInterrupt (Ctrl-C) cancels any pending multiline input and
returns to the `mylisp> ` prompt; it does NOT exit the REPL. EOF on the
initial line of a submission exits with status 0.

### 11.5 Programmatic entry point

For testability (§9 clause 11), the REPL MUST be exposed as a function
in `src/mylisp/__main__.py` (or a sibling module imported by it) with
roughly this signature:

```
def run_repl(
    inputs: Iterable[str] | None = None,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int: ...
```

When `inputs is None` the REPL reads from `sys.stdin` and uses
`readline` per §11.2. When `inputs` is a sequence (test mode), the REPL
reads lines from it, skips `readline` entirely, and exits when the
iterator is exhausted. The return value is the would-be exit status
(0 for normal exit).

The exact function name and module location are the Builder's choice;
the Critic must be able to import a documented entry point and drive the
REPL from a unit test.

---

## Clarifications

(Empty. Critic appends here only, with date and brief rationale, when SPEC
language proves genuinely ambiguous in practice.)
x  
 