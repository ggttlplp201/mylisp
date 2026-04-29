"""AST / value types for mylisp.

A unified representation: parsed S-expressions ARE runtime values for atoms,
symbols, pairs, and the empty list. Closures, builtins, and the unspecified
sentinel are runtime-only additions.

Atoms are plain Python ``int``, ``bool``, and ``str``. Compound forms use
frozen dataclasses (per AGENTS.md). The empty list ``'()`` and the
unspecified value are singletons: always use the ``EMPTY`` and ``UNSPECIFIED``
constants so identity comparison is reliable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Union

if TYPE_CHECKING:
    from .env import Env


@dataclass(frozen=True)
class Symbol:
    name: str


@dataclass(frozen=True)
class EmptyList:
    pass


EMPTY: EmptyList = EmptyList()


@dataclass(frozen=True)
class Unspecified:
    pass


UNSPECIFIED: Unspecified = Unspecified()


@dataclass(frozen=True)
class Pair:
    car: "Value"
    cdr: "Value"


@dataclass(eq=False)
class Closure:
    """A user-defined procedure. Identity-based equality (SPEC §5.7)."""

    params: tuple[str, ...]
    rest: str | None
    body: tuple["Value", ...]
    env: "Env"


@dataclass(eq=False)
class Builtin:
    """A primitive procedure. Identity-based equality (SPEC §5.7)."""

    name: str
    func: Callable[[list["Value"]], "Value"] = field(repr=False)


Value = Union[int, bool, str, Symbol, EmptyList, Unspecified, Pair, Closure, Builtin]
