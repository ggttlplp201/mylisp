STATUS: CHANGES_REQUESTED
ITERATION: 16
FINDINGS:
- src/mylisp/builtins.py:89 accepts unary `/` and returns `0` for `(/ 2)`. SPEC §5.1 explicitly defines unary behavior for `-` but not for `/`; adding reciprocal-style division is outside the §4/§5 language surface. Added `tests/acceptance/err_division_unary.*` to cover this missing edge.
NEXT_ACTIONS_FOR_BUILDER:
- Make `/` require at least two arguments, so `(/ 2)` raises `RuntimeError: arity mismatch: expected at least 2, got 1`.
- Re-run `make test acceptance lint typecheck`; the newly added acceptance test should pass without weakening existing tests.
