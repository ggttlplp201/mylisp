import pytest

from mylisp.ast import EMPTY, Pair, Symbol
from mylisp.env import Env, EvalError
from mylisp.evaluator import evaluate


def test_integer_self_evaluates():
    env = Env()
    assert evaluate(42, env) == 42


def test_negative_integer_self_evaluates():
    env = Env()
    assert evaluate(-7, env) == -7


def test_zero_self_evaluates():
    env = Env()
    assert evaluate(0, env) == 0


def test_true_self_evaluates_and_stays_bool():
    env = Env()
    result = evaluate(True, env)
    assert result is True
    assert type(result) is bool


def test_false_self_evaluates_and_stays_bool():
    env = Env()
    result = evaluate(False, env)
    assert result is False
    assert type(result) is bool


def test_string_self_evaluates():
    env = Env()
    assert evaluate("hello", env) == "hello"


def test_empty_string_self_evaluates():
    env = Env()
    assert evaluate("", env) == ""


def test_empty_list_self_evaluates():
    env = Env()
    assert evaluate(EMPTY, env) is EMPTY


def test_self_evaluation_does_not_consult_env():
    # No bindings whatsoever — literals must still evaluate.
    env = Env()
    assert evaluate(123, env) == 123
    assert evaluate("s", env) == "s"
    assert evaluate(True, env) is True


def test_symbol_resolves_to_bound_value():
    env = Env()
    env.define("x", 42)
    assert evaluate(Symbol("x"), env) == 42


def test_symbol_resolves_through_parent_frame():
    parent = Env()
    parent.define("g", "from-parent")
    child = parent.extend()
    assert evaluate(Symbol("g"), child) == "from-parent"


def test_symbol_inner_binding_shadows_outer():
    parent = Env()
    parent.define("x", 1)
    child = parent.extend({"x": 2})
    assert evaluate(Symbol("x"), child) == 2


def test_unbound_symbol_raises_with_spec_prefix():
    env = Env()
    with pytest.raises(EvalError) as exc:
        evaluate(Symbol("nope"), env)
    assert exc.value.message == "unbound symbol: nope"
    assert str(exc.value) == "RuntimeError: unbound symbol: nope"


def test_symbol_lookup_returns_compound_values_unchanged():
    env = Env()
    pair = Pair(1, Pair(2, EMPTY))
    env.define("xs", pair)
    assert evaluate(Symbol("xs"), env) is pair


def test_pair_not_yet_evaluable_raises_eval_error():
    env = Env()
    with pytest.raises(EvalError):
        evaluate(Pair(1, EMPTY), env)
