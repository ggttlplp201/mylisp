"""Shared state for the ``load`` primitive (SPEC §5.12).

``load`` is a regular builtin, but it needs two pieces of context that ordinary
primitives lack: a reference to the global environment (forms in a loaded file
evaluate against the GLOBAL env regardless of where ``load`` was called from)
and the path of the file currently being evaluated (relative loads resolve
against its directory). Both are kept here as a single mutable singleton.

``__main__.py`` calls :meth:`LoadState.init` once per interpreter invocation;
file mode also pushes the initial program file onto the source stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .env import Env


class LoadState:
    """Tracks the running interpreter's global env and active source stack.

    Stack entries may be ``None``, indicating that the currently executing
    code has no associated source file (REPL, ``-e``, prelude, or a closure
    defined in any of those contexts). A ``None`` on top forces relative
    ``load`` paths in §5.12.1 to fall back to ``Path.cwd()``.
    """

    __slots__ = ("global_env", "_source_stack")

    def __init__(self) -> None:
        self.global_env: "Env | None" = None
        self._source_stack: list[Path | None] = []

    def init(self, global_env: "Env") -> None:
        """Bind the global env and reset the source stack."""
        self.global_env = global_env
        self._source_stack = []

    def current_source(self) -> Path | None:
        """Return the source of the form currently being evaluated, if any."""
        if self._source_stack:
            return self._source_stack[-1]
        return None

    def push(self, path: Path | None) -> None:
        self._source_stack.append(path)

    def pop(self) -> None:
        self._source_stack.pop()


STATE: LoadState = LoadState()
