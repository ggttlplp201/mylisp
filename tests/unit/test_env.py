import pytest

from mylisp.ast import EMPTY, Pair, Symbol
from mylisp.env import Env, EvalError


def test_define_and_lookup_in_single_frame():
    env = Env()
    env.define("x", 42)
    assert env.lookup("x") == 42


def test_lookup_unbound_raises_with_spec_prefix():
    env = Env()
    with pytest.raises(EvalError) as exc:
        env.lookup("missing")
    assert exc.value.message == "unbound symbol: missing"
    assert str(exc.value) == "RuntimeError: unbound symbol: missing"


def test_define_overwrites_existing_in_same_frame():
    env = Env()
    env.define("x", 1)
    env.define("x", 2)
    assert env.lookup("x") == 2


def test_extend_creates_child_with_parent_visible():
    parent = Env()
    parent.define("x", 1)
    child = parent.extend()
    assert child.lookup("x") == 1


def test_extend_with_bindings_initializes_child_frame():
    parent = Env()
    parent.define("x", 1)
    child = parent.extend({"y": 2})
    assert child.lookup("y") == 2
    assert child.lookup("x") == 1


def test_child_define_shadows_parent_without_mutating_it():
    parent = Env()
    parent.define("x", 1)
    child = parent.extend()
    child.define("x", 2)
    assert child.lookup("x") == 2
    assert parent.lookup("x") == 1


def test_assign_mutates_innermost_existing_binding_in_parent():
    parent = Env()
    parent.define("x", 1)
    child = parent.extend()
    child.assign("x", 99)
    assert parent.lookup("x") == 99
    assert child.lookup("x") == 99


def test_assign_unbound_raises():
    env = Env()
    with pytest.raises(EvalError) as exc:
        env.assign("nope", 1)
    assert exc.value.message == "unbound symbol: nope"


def test_assign_targets_innermost_shadow_when_present():
    parent = Env()
    parent.define("x", 1)
    child = parent.extend()
    child.define("x", 2)
    child.assign("x", 3)
    assert child.lookup("x") == 3
    # Parent's binding is untouched because the child's shadow took the assign.
    assert parent.lookup("x") == 1


def test_lookup_walks_multiple_levels():
    grand = Env()
    grand.define("g", "from-grand")
    parent = grand.extend()
    parent.define("p", Symbol("p-sym"))
    child = parent.extend()
    child.define("c", 0)
    assert child.lookup("c") == 0
    assert child.lookup("p") == Symbol("p-sym")
    assert child.lookup("g") == "from-grand"


def test_init_copies_bindings_dict():
    src = {"x": 1}
    env = Env(src)
    src["x"] = 999
    assert env.lookup("x") == 1


def test_stores_compound_values():
    env = Env()
    pair: Pair = Pair(1, Pair(2, EMPTY))
    env.define("xs", pair)
    assert env.lookup("xs") == pair
