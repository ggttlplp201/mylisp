"""Primitive procedures for mylisp. See SPEC §5.1, §5.2, §5.4, §5.7, §5.8, §5.12.

Each primitive is wrapped as a :class:`Builtin`. Arity and type checks
raise :class:`EvalError` with the SPEC §5.9 prefix the test suite expects.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from .ast import (
    EMPTY,
    UNSPECIFIED,
    Builtin,
    EmptyList,
    Pair,
    Symbol,
    Value,
)
from .env import EvalError
from .printer import display as _display
from .printer import write as _write


def _exact_arity(name: str, args: list[Value], n: int) -> None:
    if len(args) != n:
        raise EvalError(f"arity mismatch: expected {n}, got {len(args)}")


def _at_least(name: str, args: list[Value], n: int) -> None:
    if len(args) < n:
        raise EvalError(
            f"arity mismatch: expected at least {n}, got {len(args)}"
        )


def _check_int(value: Value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise EvalError(f"type error: expected integer, got {_write(value)}")
    return value


def _check_string(value: Value) -> str:
    if not isinstance(value, str):
        raise EvalError(f"type error: expected string, got {_write(value)}")
    return value


def _check_pair(value: Value) -> Pair:
    if not isinstance(value, Pair):
        raise EvalError(f"type error: expected pair, got {_write(value)}")
    return value


def _trunc_div(a: int, b: int) -> int:
    sign = -1 if (a < 0) ^ (b < 0) else 1
    return sign * (abs(a) // abs(b))


def _trunc_rem(a: int, b: int) -> int:
    return a - _trunc_div(a, b) * b


def _b_add(args: list[Value]) -> Value:
    total = 0
    for a in args:
        total += _check_int(a)
    return total


def _b_mul(args: list[Value]) -> Value:
    total = 1
    for a in args:
        total *= _check_int(a)
    return total


def _b_sub(args: list[Value]) -> Value:
    _at_least("-", args, 1)
    head = _check_int(args[0])
    if len(args) == 1:
        return -head
    for a in args[1:]:
        head -= _check_int(a)
    return head


def _b_div(args: list[Value]) -> Value:
    _at_least("/", args, 2)
    head = _check_int(args[0])
    for a in args[1:]:
        d = _check_int(a)
        if d == 0:
            raise EvalError("division by zero")
        head = _trunc_div(head, d)
    return head


def _b_quotient(args: list[Value]) -> Value:
    _exact_arity("quotient", args, 2)
    a = _check_int(args[0])
    b = _check_int(args[1])
    if b == 0:
        raise EvalError("division by zero")
    return _trunc_div(a, b)


def _b_remainder(args: list[Value]) -> Value:
    _exact_arity("remainder", args, 2)
    a = _check_int(args[0])
    b = _check_int(args[1])
    if b == 0:
        raise EvalError("division by zero")
    return _trunc_rem(a, b)


def _b_modulo(args: list[Value]) -> Value:
    _exact_arity("modulo", args, 2)
    a = _check_int(args[0])
    b = _check_int(args[1])
    if b == 0:
        raise EvalError("division by zero")
    return a % b


def _make_cmp(op: Callable[[int, int], bool]) -> Callable[[list[Value]], Value]:
    def impl(args: list[Value]) -> Value:
        _exact_arity("cmp", args, 2)
        a = _check_int(args[0])
        b = _check_int(args[1])
        return op(a, b)

    return impl


def _b_string_length(args: list[Value]) -> Value:
    _exact_arity("string-length", args, 1)
    return len(_check_string(args[0]))


def _b_string_append(args: list[Value]) -> Value:
    parts: list[str] = []
    for a in args:
        parts.append(_check_string(a))
    return "".join(parts)


def _b_cons(args: list[Value]) -> Value:
    _exact_arity("cons", args, 2)
    return Pair(args[0], args[1])


def _b_car(args: list[Value]) -> Value:
    _exact_arity("car", args, 1)
    return _check_pair(args[0]).car


def _b_cdr(args: list[Value]) -> Value:
    _exact_arity("cdr", args, 1)
    return _check_pair(args[0]).cdr


def _b_list(args: list[Value]) -> Value:
    result: Value = EMPTY
    for a in reversed(args):
        result = Pair(a, result)
    return result


def _b_null_p(args: list[Value]) -> Value:
    _exact_arity("null?", args, 1)
    return isinstance(args[0], EmptyList)


def _b_pair_p(args: list[Value]) -> Value:
    _exact_arity("pair?", args, 1)
    return isinstance(args[0], Pair)


def _b_length(args: list[Value]) -> Value:
    _exact_arity("length", args, 1)
    head = args[0]
    n = 0
    cur: Value = head
    while isinstance(cur, Pair):
        n += 1
        cur = cur.cdr
    if not isinstance(cur, EmptyList):
        raise EvalError(f"type error: expected proper list, got {_write(head)}")
    return n


def _b_eq_p(args: list[Value]) -> Value:
    _exact_arity("eq?", args, 2)
    a, b = args[0], args[1]
    if isinstance(a, (Pair,)) or isinstance(b, (Pair,)):
        return a is b
    return a == b


def _b_equal_p(args: list[Value]) -> Value:
    _exact_arity("equal?", args, 2)
    return args[0] == args[1]


def _b_eq_num(args: list[Value]) -> Value:
    _exact_arity("=", args, 2)
    return _check_int(args[0]) == _check_int(args[1])


def _b_display(args: list[Value]) -> Value:
    _exact_arity("display", args, 1)
    from .evaluator import LOADER_STATE

    LOADER_STATE.active_output().write(_display(args[0]))
    return UNSPECIFIED


def _b_write(args: list[Value]) -> Value:
    _exact_arity("write", args, 1)
    from .evaluator import LOADER_STATE

    LOADER_STATE.active_output().write(_write(args[0]))
    return UNSPECIFIED


def _b_newline(args: list[Value]) -> Value:
    _exact_arity("newline", args, 0)
    from .evaluator import LOADER_STATE

    LOADER_STATE.active_output().write("\n")
    return UNSPECIFIED


def _resolve_load_path(raw: str) -> Path:
    """Apply SPEC §5.12.1 path resolution to a raw ``load`` argument."""
    from .evaluator import LOADER_STATE

    path = Path(raw)
    if path.is_absolute():
        return path
    current = LOADER_STATE.current_source()
    base = current.parent if current is not None else Path.cwd()
    return base / path


def _read_loaded_source(resolved: Path) -> str:
    resolved_str = str(resolved)
    try:
        return resolved.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise EvalError(
            f"load failed: cannot read {resolved_str}: file not found"
        ) from exc
    except IsADirectoryError as exc:
        raise EvalError(
            f"load failed: cannot read {resolved_str}: is a directory"
        ) from exc
    except PermissionError as exc:
        raise EvalError(
            f"load failed: cannot read {resolved_str}: permission denied"
        ) from exc
    except UnicodeDecodeError as exc:
        raise EvalError(
            f"load failed: cannot read {resolved_str}: invalid UTF-8"
        ) from exc
    except OSError as exc:
        reason = exc.strerror or "I/O error"
        raise EvalError(
            f"load failed: cannot read {resolved_str}: {reason}"
        ) from exc


def _b_load(args: list[Value]) -> Value:
    _exact_arity("load", args, 1)
    path_str = _check_string(args[0])

    from .evaluator import LOADER_STATE, evaluate
    from .lexer import LexError, tokenize
    from .parser import ParseError, parse

    resolved = _resolve_load_path(path_str)
    resolved_str = str(resolved)
    source = _read_loaded_source(resolved)

    try:
        tokens = tokenize(source)
    except LexError as exc:
        raise LexError(exc.message, exc.line, exc.col, source=resolved_str) from None

    try:
        exprs = parse(tokens)
    except ParseError as exc:
        raise ParseError(
            exc.message, exc.line, exc.col, source=resolved_str
        ) from None

    if LOADER_STATE.global_env is None:
        raise EvalError("load failed: interpreter state not initialized")

    LOADER_STATE.push(resolved)
    try:
        for expr in exprs:
            evaluate(expr, LOADER_STATE.global_env)
    finally:
        LOADER_STATE.pop()
    return UNSPECIFIED


_BUILTIN_TABLE: dict[str, Callable[[list[Value]], Value]] = {
    "+": _b_add,
    "-": _b_sub,
    "*": _b_mul,
    "/": _b_div,
    "quotient": _b_quotient,
    "remainder": _b_remainder,
    "modulo": _b_modulo,
    "<": _make_cmp(lambda a, b: a < b),
    "<=": _make_cmp(lambda a, b: a <= b),
    ">": _make_cmp(lambda a, b: a > b),
    ">=": _make_cmp(lambda a, b: a >= b),
    "=": _b_eq_num,
    "string-length": _b_string_length,
    "string-append": _b_string_append,
    "cons": _b_cons,
    "car": _b_car,
    "cdr": _b_cdr,
    "list": _b_list,
    "null?": _b_null_p,
    "pair?": _b_pair_p,
    "length": _b_length,
    "eq?": _b_eq_p,
    "equal?": _b_equal_p,
    "display": _b_display,
    "write": _b_write,
    "newline": _b_newline,
    "load": _b_load,
}


def builtin_bindings() -> dict[str, Value]:
    """Return a fresh dict of name -> :class:`Builtin` for env seeding."""
    return {name: Builtin(name, fn) for name, fn in _BUILTIN_TABLE.items()}


__all__ = ["builtin_bindings", "Symbol"]
