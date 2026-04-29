"""Tree-walking evaluator. See SPEC §5.

Special forms are dispatched by symbol head before procedure application.
``define`` and ``set!`` return :data:`UNSPECIFIED` so the printer omits them
at the top level; ``cond`` does the same when no clause matches.
"""

from __future__ import annotations

from typing import Callable

from .ast import (
    EMPTY,
    UNSPECIFIED,
    Builtin,
    Closure,
    EmptyList,
    Pair,
    Symbol,
    Value,
)
from .env import Env, EvalError
from .printer import write as _write


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
    if isinstance(expr, Pair):
        head = expr.car
        if isinstance(head, Symbol):
            form = _SPECIAL_FORMS.get(head.name)
            if form is not None:
                return form(_pair_to_list(expr.cdr), env)
        proc = evaluate(head, env)
        args = [evaluate(a, env) for a in _pair_to_list(expr.cdr)]
        return _apply(proc, args)
    raise EvalError(f"cannot evaluate: {expr!r}")


def _pair_to_list(value: Value) -> list[Value]:
    """Walk a proper list of operands; raise on improper list."""
    out: list[Value] = []
    cur: Value = value
    while isinstance(cur, Pair):
        out.append(cur.car)
        cur = cur.cdr
    if not isinstance(cur, EmptyList):
        raise EvalError(f"malformed list in source: {_write(value)}")
    return out


def _apply(proc: Value, args: list[Value]) -> Value:
    if isinstance(proc, Builtin):
        return proc.func(args)
    if isinstance(proc, Closure):
        frame: dict[str, Value] = {}
        if proc.rest is None:
            if len(args) != len(proc.params):
                raise EvalError(
                    f"arity mismatch: expected {len(proc.params)}, got {len(args)}"
                )
            for name, val in zip(proc.params, args):
                frame[name] = val
        else:
            if len(args) < len(proc.params):
                raise EvalError(
                    "arity mismatch: expected at least "
                    f"{len(proc.params)}, got {len(args)}"
                )
            for name, val in zip(proc.params, args):
                frame[name] = val
            rest_list: Value = EMPTY
            for v in reversed(args[len(proc.params):]):
                rest_list = Pair(v, rest_list)
            frame[proc.rest] = rest_list
        call_env = proc.env.extend(frame)
        body = _process_internal_defines(list(proc.body), call_env)
        return _eval_body(body, call_env)
    raise EvalError(f"not a procedure: {_write(proc)}")


def _process_internal_defines(body: list[Value], env: Env) -> list[Value]:
    """Pre-bind any leading internal ``define``s in ``env`` (SPEC §5.5.5)."""
    i = 0
    while i < len(body):
        expr = body[i]
        if isinstance(expr, Pair) and isinstance(expr.car, Symbol) and expr.car.name == "define":
            _eval_define(_pair_to_list(expr.cdr), env)
            i += 1
            continue
        break
    for expr in body[i:]:
        if isinstance(expr, Pair) and isinstance(expr.car, Symbol) and expr.car.name == "define":
            raise EvalError("define is only permitted at the head of a body")
    return body[i:]


def _eval_body(body: list[Value], env: Env) -> Value:
    if not body:
        raise EvalError("empty body")
    result: Value = UNSPECIFIED
    for expr in body:
        result = evaluate(expr, env)
    return result


def _eval_quote(args: list[Value], env: Env) -> Value:
    if len(args) != 1:
        raise EvalError(f"arity mismatch: expected 1, got {len(args)}")
    return args[0]


def _eval_if(args: list[Value], env: Env) -> Value:
    if len(args) != 3:
        raise EvalError(f"arity mismatch: expected 3, got {len(args)}")
    cond = evaluate(args[0], env)
    if cond is False:
        return evaluate(args[2], env)
    return evaluate(args[1], env)


def _check_symbol(value: Value, ctx: str) -> Symbol:
    if not isinstance(value, Symbol):
        raise EvalError(f"{ctx}: expected symbol, got {_write(value)}")
    return value


def _eval_define(args: list[Value], env: Env) -> Value:
    if len(args) < 2:
        raise EvalError(f"arity mismatch: expected at least 2, got {len(args)}")
    target = args[0]
    if isinstance(target, Symbol):
        if len(args) != 2:
            raise EvalError("define: expected (define <name> <expr>)")
        env.define(target.name, evaluate(args[1], env))
        return UNSPECIFIED
    if isinstance(target, Pair):
        head = _check_symbol(target.car, "define")
        params, rest = _parse_formals(target.cdr)
        body = tuple(args[1:])
        env.define(head.name, Closure(params, rest, body, env))
        return UNSPECIFIED
    raise EvalError(f"define: bad target {_write(target)}")


def _eval_set(args: list[Value], env: Env) -> Value:
    if len(args) != 2:
        raise EvalError(f"arity mismatch: expected 2, got {len(args)}")
    name = _check_symbol(args[0], "set!")
    env.assign(name.name, evaluate(args[1], env))
    return UNSPECIFIED


def _parse_formals(formals: Value) -> tuple[tuple[str, ...], str | None]:
    """Parse a lambda/define parameter list. Supports the three SPEC forms."""
    if isinstance(formals, Symbol):
        return (), formals.name
    params: list[str] = []
    cur: Value = formals
    while isinstance(cur, Pair):
        params.append(_check_symbol(cur.car, "lambda").name)
        cur = cur.cdr
    if isinstance(cur, EmptyList):
        return tuple(params), None
    if isinstance(cur, Symbol):
        return tuple(params), cur.name
    raise EvalError(f"lambda: bad formals {_write(formals)}")


def _eval_lambda(args: list[Value], env: Env) -> Value:
    if len(args) < 2:
        raise EvalError(f"arity mismatch: expected at least 2, got {len(args)}")
    params, rest = _parse_formals(args[0])
    body = tuple(args[1:])
    return Closure(params, rest, body, env)


def _eval_let(args: list[Value], env: Env) -> Value:
    if len(args) < 2:
        raise EvalError("let: expected bindings and body")
    bindings = _parse_bindings(args[0], "let")
    frame: dict[str, Value] = {}
    for name, expr in bindings:
        frame[name] = evaluate(expr, env)
    new_env = env.extend(frame)
    body = _process_internal_defines(list(args[1:]), new_env)
    return _eval_body(body, new_env)


def _eval_let_star(args: list[Value], env: Env) -> Value:
    if len(args) < 2:
        raise EvalError("let*: expected bindings and body")
    bindings = _parse_bindings(args[0], "let*")
    new_env = env
    for name, expr in bindings:
        new_env = new_env.extend({name: evaluate(expr, new_env)})
    body = _process_internal_defines(list(args[1:]), new_env)
    return _eval_body(body, new_env)


def _eval_letrec(args: list[Value], env: Env) -> Value:
    if len(args) < 2:
        raise EvalError("letrec: expected bindings and body")
    bindings = _parse_bindings(args[0], "letrec")
    new_env = env.extend({name: UNSPECIFIED for name, _ in bindings})
    for name, expr in bindings:
        new_env.define(name, evaluate(expr, new_env))
    body = _process_internal_defines(list(args[1:]), new_env)
    return _eval_body(body, new_env)


def _parse_bindings(value: Value, ctx: str) -> list[tuple[str, Value]]:
    out: list[tuple[str, Value]] = []
    cur: Value = value
    while isinstance(cur, Pair):
        clause = cur.car
        if not isinstance(clause, Pair) or not isinstance(clause.cdr, Pair):
            raise EvalError(f"{ctx}: malformed binding {_write(clause)}")
        rest = clause.cdr
        if not isinstance(rest.cdr, EmptyList):
            raise EvalError(f"{ctx}: malformed binding {_write(clause)}")
        name = _check_symbol(clause.car, ctx).name
        out.append((name, rest.car))
        cur = cur.cdr
    if not isinstance(cur, EmptyList):
        raise EvalError(f"{ctx}: malformed bindings {_write(value)}")
    return out


def _eval_cond(args: list[Value], env: Env) -> Value:
    for clause in args:
        if not isinstance(clause, Pair):
            raise EvalError(f"cond: malformed clause {_write(clause)}")
        test = clause.car
        body = _pair_to_list(clause.cdr)
        if isinstance(test, Symbol) and test.name == "else":
            if not body:
                raise EvalError("cond: empty else clause")
            return _eval_body(body, env)
        result = evaluate(test, env)
        if result is False:
            continue
        if not body:
            return result
        return _eval_body(body, env)
    return UNSPECIFIED


def _eval_and(args: list[Value], env: Env) -> Value:
    if not args:
        return True
    last: Value = True
    for expr in args:
        last = evaluate(expr, env)
        if last is False:
            return False
    return last


def _eval_or(args: list[Value], env: Env) -> Value:
    for expr in args:
        result = evaluate(expr, env)
        if result is not False:
            return result
    return False


def _eval_begin(args: list[Value], env: Env) -> Value:
    if not args:
        raise EvalError("arity mismatch: expected at least 1, got 0")
    return _eval_body(args, env)


_SPECIAL_FORMS: dict[str, Callable[[list[Value], Env], Value]] = {
    "quote": _eval_quote,
    "if": _eval_if,
    "define": _eval_define,
    "set!": _eval_set,
    "lambda": _eval_lambda,
    "let": _eval_let,
    "let*": _eval_let_star,
    "letrec": _eval_letrec,
    "cond": _eval_cond,
    "and": _eval_and,
    "or": _eval_or,
    "begin": _eval_begin,
}
