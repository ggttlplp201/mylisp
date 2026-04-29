"""Value formatting for mylisp. See SPEC §6.

Two modes: ``write`` (machine-readable, strings quoted) and ``display``
(human-readable, strings unquoted). Unspecified values render to the empty
string and must NOT be printed at the REPL or as top-level results.
"""

from __future__ import annotations

from .ast import (
    Builtin,
    Closure,
    EmptyList,
    Pair,
    Symbol,
    Unspecified,
    Value,
)


_WRITE_ESCAPES: dict[str, str] = {
    "\\": "\\\\",
    '"': '\\"',
    "\n": "\\n",
    "\t": "\\t",
}


def _escape_string(s: str) -> str:
    return "".join(_WRITE_ESCAPES.get(c, c) for c in s)


def _format_pair(p: Pair, mode: str) -> str:
    parts: list[str] = [_format(p.car, mode)]
    cdr: Value = p.cdr
    while isinstance(cdr, Pair):
        parts.append(_format(cdr.car, mode))
        cdr = cdr.cdr
    if isinstance(cdr, EmptyList):
        return "(" + " ".join(parts) + ")"
    return "(" + " ".join(parts) + " . " + _format(cdr, mode) + ")"


def _format(value: Value, mode: str) -> str:
    if isinstance(value, bool):
        return "#t" if value else "#f"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        if mode == "write":
            return '"' + _escape_string(value) + '"'
        return value
    if isinstance(value, EmptyList):
        return "()"
    if isinstance(value, Symbol):
        return value.name
    if isinstance(value, Pair):
        return _format_pair(value, mode)
    if isinstance(value, Closure):
        return "#<procedure>"
    if isinstance(value, Builtin):
        return f"#<builtin {value.name}>"
    if isinstance(value, Unspecified):
        return ""
    raise TypeError(f"unprintable value: {value!r}")


def write(value: Value) -> str:
    """Return the write-mode representation of ``value`` (SPEC §6)."""
    return _format(value, "write")


def display(value: Value) -> str:
    """Return the display-mode representation of ``value`` (SPEC §6)."""
    return _format(value, "display")
