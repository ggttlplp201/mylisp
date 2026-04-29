"""AST / value types for mylisp.

A unified representation: parsed S-expressions ARE runtime values for atoms,
symbols, pairs, and the empty list. Closures and builtins are added later.

Atoms are plain Python ``int``, ``bool``, and ``str``. Compound forms use
frozen dataclasses (per AGENTS.md). The empty list ``'()`` is a singleton:
always use the ``EMPTY`` constant so identity comparison is reliable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class Symbol:
    name: str


@dataclass(frozen=True)
class EmptyList:
    pass


EMPTY: EmptyList = EmptyList()


@dataclass(frozen=True)
class Pair:
    car: "Value"
    cdr: "Value"


Value = Union[int, bool, str, Symbol, EmptyList, Pair]
