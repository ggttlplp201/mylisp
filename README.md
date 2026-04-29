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

## Specification

See [SPEC.md](SPEC.md) for the full language and project contract.
