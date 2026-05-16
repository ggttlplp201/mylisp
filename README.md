# mylisp

A small tree-walking interpreter for a Scheme-flavored Lisp, written in
Python 3.11+ with no third-party runtime dependencies.

> **Note:** This was an experimental project run entirely by Claude Code,
> Codex, and Ralph. No human intervention was involved at all in writing
> source code. The main purpose was to test techniques of harness
> engineering for autonomous workflows in future projects that are more
> complex. The initial language was completed in around 15 iterations;
> the prelude / `load` / REPL features described below were added in a
> later run of the same harness. See the Markdown docs in the repo
> ([SPEC.md](SPEC.md) and `PLAN.md`) for more info.

## Installation

```
pip install -e .[dev]
```

## Example

```
$ ./mylisp -e "(+ 1 2 3)"
6

$ ./mylisp -e "(map (lambda (x) (* x x)) '(1 2 3 4 5))"
(1 4 9 16 25)

$ ./mylisp
mylisp> (define (fact n) (if (= n 0) 1 (* n (fact (- n 1)))))
mylisp> (fact 10)
3628800
mylisp> :load examples/use_load.lisp
mylisp> :quit
```

## Language

mylisp implements a strict subset of Scheme:

- **Special forms** — `quote`, `if`, `cond`, `and`, `or`, `define`, `set!`,
  `lambda`, `let`, `let*`, `letrec`, `begin`.
- **Numbers** — arbitrary-precision integers only. No floats. Operators:
  `+ - * / quotient remainder modulo < <= > >= =`.
- **Pairs and lists** — `cons`, `car`, `cdr`, `list`, `null?`, `pair?`, `length`.
- **Strings** — immutable, with `string-length` and `string-append`.
- **Equality** — `eq?`, `equal?`.
- **Prelude (Lisp-defined standard library)** — `not`, `list?`, all 12
  `c[ad]+r` selectors, `append`, `reverse`, `map`, `filter`, `foldl`, `foldr`,
  `member`, `memq`, `assoc`, `assq`. Auto-loaded at startup.
- **`load`** — `(load "path")` reads, parses, and evaluates a Lisp file
  against the global environment. Relative paths resolve against the file
  containing the call (and against the working directory in REPL / `-e`
  mode). Closures capture their defining file's source path.
- **REPL** — multiline input, persistent history via `readline`
  (`~/.mylisp_history`), and the directives `:quit`, `:help`, `:load`, `:env`.

Out of scope by design: macros, continuations, `eval` of strings, floats,
vectors / hash tables / records, mutable pairs, characters as a distinct
type, anything resembling a module system beyond `load`. See SPEC §2.

## How this was built

This project used a two-agent autonomous loop (the "Ralph" technique) to build the interpreter from a frozen specification.

### The harness

- **SPEC.md** — Frozen contract describing every required feature. Never edited by agents.
- **Builder agent** (Claude Code) — Reads SPEC, PLAN, and REVIEW; picks the highest-priority task; makes one focused commit per turn.
- **Critic agent** (Codex) — Runs the full test suite, inspects recent commits, writes adversarial acceptance tests, and produces REVIEW.md verdicts.
- **Orchestrator** — A bash script that alternates Builder and Critic turns until the project meets the SPEC's "Definition of Done" or hits a max iteration count.
- **Role-enforcement git hook** — A pre-commit hook that rejects commits if an agent tries to touch files outside its role (e.g., Builder modifying acceptance tests).

### The directory layout
```
mylisp/
├── SPEC.md                  # immutable contract
├── PLAN.md                  # task list, agents update this
├── AGENTS.md                # build/test commands and conventions
├── REVIEW.md                # critic's latest verdict
├── prompts/
│   ├── BUILDER_PROMPT.md
│   └── CRITIC_PROMPT.md
├── scripts/
│   ├── orchestrate.sh       # main loop
│   ├── ralph-builder.sh     # Claude Code invocation
│   ├── ralph-critic.sh      # Codex invocation
│   └── check-progress.sh    # stuck-detector
├── .githooks/pre-commit     # role enforcement
└── src/, tests/, examples/
```

### Setup

1. Wrote the SPEC, scaffolded an empty project structure (folders + empty Python modules), and wrote 8 initial acceptance tests by hand to seed the Critic.
2. Configured a pre-commit git hook keyed off `.ralph/role` that rejects:
   - Anyone but `human` modifying SPEC.md
   - Builder touching `tests/acceptance/` or REVIEW.md
   - Critic touching `src/`, `tests/unit/`, or PLAN.md
3. Wrote prompts for both agents that emphasize: read context first, do exactly one task per turn, never weaken tests, exit after one commit.
4. Tagged the empty scaffold (`scaffold-v0`) as a rollback point.

### Running it

Each iteration: orchestrator checks if done → runs Builder OR Critic → swaps the lock → next iteration. Done condition is `make acceptance` passing AND `STATUS: APPROVED` in REVIEW.md.

### Results

**Initial run** (the core interpreter, §4–§5 of the original SPEC):

- Completed in ~15 iterations
- 49/49 acceptance tests, 75/75 unit tests
- Lint and typecheck clean throughout
- Zero human edits to source code

**Follow-on run** (prelude / `load` / REPL upgrades — §5.10, §5.12, §11):

- The same harness was run again after the human amended SPEC.md to add
  three new sections. The Builder implemented the features; the Critic
  added matching acceptance tests and caught real bugs along the way
  (e.g. `member` / `memq` / `assoc` / `assq` returning before validating
  list properness, hardcoded paths in test fixtures, `(/ x)` silently
  accepting unary, prelude not loading in `-e` mode).
- Ended at 72/72 acceptance tests, 109/109 unit tests
- Three human interventions during this run: amend SPEC, harden the
  orchestrator (timeout detection + codex sandbox permissions), and
  unstick one path-bound test the Critic flagged but didn't fix in-turn.
  All source code still written by the Builder.


## Specification

See [SPEC.md](SPEC.md) for the full language and project contract.
