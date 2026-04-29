# Agent operations

## Build
- Install: `pip install -e .[dev]`
- All checks: `make all`
- Single test: `pytest tests/unit/test_lexer.py::test_integer -q`

## Conventions
- Python 3.11+. Type hints required (`mypy --strict` enforces).
- No third-party runtime deps. stdlib only.
- AST nodes: frozen dataclasses in `src/mylisp/ast.py`.
- Errors raise `MylispError` subclasses; CLI catches and formats.
- Avoid `Any`. Use `typing.Union` or proper sum types.

## Anti-patterns observed (grow this list)
- (empty — populate as the loop runs)
