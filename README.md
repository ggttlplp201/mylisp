# mylisp

A small tree-walking interpreter for a Scheme-flavored Lisp, written in
Python 3.11+ with no third-party runtime dependencies.

> **Note:** This was an experimental project run entirely by Claude Code,
> Codex, and Ralph. No human intervention was involved at all. The main
> purpose was to test techniques of harness engineering for autonoumous
> workflows in future projects that are more complex. The code base
> and all testing was completed in around 15 iterations. See the
> Markdown docs in the repo ([SPEC.md](SPEC.md) and `PLAN.md`)
> for for info.

## Installation

```
pip install -e .[dev]
```

## Example

```
$ ./mylisp -e "(+ 1 2 3)"
6
```

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

- Completed in ~15 iterations
- 49/49 acceptance tests passing
- 75/75 unit tests passing
- Lint and typecheck clean throughout
- Zero human edits to source code


## Specification

See [SPEC.md](SPEC.md) for the full language and project contract.
