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
    assert evaluate("s", env) is "s" or evaluate("s", env) == "s"
    assert evaluate(True, env) is True


def test_symbol_not_yet_evaluable_raises_eval_error():
    # Symbol/Pair handling lands in subsequent commits; until then the
    # evaluator must surface a RuntimeError, not crash with an unrelated
    # Python exception.
    env = Env()
    with pytest.raises(EvalError):
        evaluate(Symbol("foo"), env)


def test_pair_not_yet_evaluable_raises_eval_error():
    env = Env()
    with pytest.raises(EvalError):
        evaluate(Pair(1, EMPTY), env)
