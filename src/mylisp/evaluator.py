"""Tree-walking evaluator. See SPEC §5.

This iteration handles self-evaluating literals and symbol lookup.
Special forms and procedure application are added in later commits.
"""

from __future__ import annotations

from .ast import EmptyList, Symbol, Value
from .env import Env, EvalError


def evaluate(expr: Value, env: Env) -> Value:
    """Evaluate ``expr`` under ``env`` and return the resulting value."""
    if isinstance(expr, bool):
        return expr
    if isinstance(expr, int):
        return expr
    if isinstance(expr, str):
        return expr
    if isinstance(expr, EmptyList):
        return expr
    if isinstance(expr, Symbol):
        return env.lookup(expr.name)
    raise EvalError(f"cannot evaluate: {expr!r}")
