"""Environment frames for mylisp. See SPEC §5.5.3, §5.5.4, §5.5.5, §5.9.

An ``Env`` is a chain of frames. The innermost frame is searched first;
``define`` always inserts into the innermost frame, while ``assign`` (set!)
walks the chain to mutate an existing binding. Lookups raise an
``EvalError`` formatted with the ``unbound symbol:`` prefix required by
SPEC §5.9.
"""

from __future__ import annotations

from . import MylispError
from .ast import Value


class EvalError(MylispError):
    """Runtime error raised by the evaluator. Formats as ``RuntimeError: ...``."""

    def __init__(self, message: str) -> None:
        super().__init__(f"RuntimeError: {message}")
        self.message: str = message


class Env:
    """Lexically chained frame of name -> value bindings."""

    __slots__ = ("_frame", "_parent")

    def __init__(
        self,
        bindings: dict[str, Value] | None = None,
        parent: Env | None = None,
    ) -> None:
        self._frame: dict[str, Value] = {} if bindings is None else dict(bindings)
        self._parent: Env | None = parent

    def define(self, name: str, value: Value) -> None:
        """Bind ``name`` to ``value`` in the innermost frame, shadowing any outer binding."""
        self._frame[name] = value

    def lookup(self, name: str) -> Value:
        """Return the value for ``name``, walking outward; raise on miss."""
        env: Env | None = self
        while env is not None:
            if name in env._frame:
                return env._frame[name]
            env = env._parent
        raise EvalError(f"unbound symbol: {name}")

    def assign(self, name: str, value: Value) -> None:
        """Mutate the innermost existing binding for ``name``; raise if absent."""
        env: Env | None = self
        while env is not None:
            if name in env._frame:
                env._frame[name] = value
                return
            env = env._parent
        raise EvalError(f"unbound symbol: {name}")

    def extend(self, bindings: dict[str, Value] | None = None) -> Env:
        """Return a new child env with ``self`` as its parent."""
        return Env(bindings, parent=self)
