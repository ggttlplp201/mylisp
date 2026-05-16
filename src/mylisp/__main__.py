"""mylisp CLI entry point. See SPEC §1, §6, §5.9.

Three modes:

* ``mylisp <file.lisp>`` — read the file, evaluate each top-level expression,
  print non-unspecified results in write form.
* ``mylisp -e "<expr>"`` — evaluate one expression and print it.
* ``mylisp`` — start a REPL on stdin/stdout.

LexError, ParseError, and RuntimeError surface to stderr without a traceback;
the REPL catches them and continues, while file/-e modes exit 1.
"""

from __future__ import annotations

import io
import sys
from importlib.resources import files
from pathlib import Path
from typing import Optional, cast

from . import MylispError
from .ast import Unspecified
from .builtins import builtin_bindings
from .env import Env
from .evaluator import LOADER_STATE, evaluate
from .lexer import tokenize
from .parser import parse
from .printer import write


class PreludeLoadError(MylispError):
    """Raised when ``prelude.lisp`` fails to load. See SPEC §5.10."""

    def __init__(self, message: str) -> None:
        super().__init__(f"RuntimeError: prelude load failed: {message}")
        self.message: str = message


def _load_prelude(env: Env) -> None:
    """Read and evaluate ``prelude.lisp`` against ``env`` (SPEC §5.10, §5.11)."""
    try:
        source = files("mylisp").joinpath("prelude.lisp").read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        raise PreludeLoadError(f"cannot read prelude.lisp: {exc}") from exc
    try:
        tokens = tokenize(source)
        exprs = parse(tokens)
        for expr in exprs:
            evaluate(expr, env)
    except MylispError as exc:
        inner = getattr(exc, "message", None)
        msg = inner if isinstance(inner, str) else str(exc)
        raise PreludeLoadError(msg) from exc


def _make_global_env() -> Env:
    env = Env(builtin_bindings())
    LOADER_STATE.init(env)
    _load_prelude(env)
    return env


def _run_program(source: str, env: Env) -> None:
    """Tokenize, parse, and evaluate ``source``; print top-level results."""
    tokens = tokenize(source)
    exprs = parse(tokens)
    for expr in exprs:
        result = evaluate(expr, env)
        if not isinstance(result, Unspecified):
            sys.stdout.write(write(result) + "\n")


def _run_file(path: str) -> int:
    # SPEC §5.11: the prelude must be fully evaluated before the user file is
    # read; build the global env first so a prelude failure surfaces with its
    # dedicated prefix before any I/O on the user file.
    try:
        env = _make_global_env()
    except MylispError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    try:
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        sys.stderr.write(f"mylisp: cannot read {path}: {exc}\n")
        return 1
    file_path = Path(path).resolve()
    LOADER_STATE.push(file_path)
    try:
        _run_program(source, env)
    except MylispError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    finally:
        LOADER_STATE.pop()
    return 0


def _run_expr(source: str) -> int:
    try:
        env = _make_global_env()
        _run_program(source, env)
    except MylispError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        from .repl import run_repl

        return run_repl()
    if args[0] == "-e":
        if len(args) != 2:
            sys.stderr.write("mylisp: -e requires exactly one argument\n")
            return 1
        return _run_expr(args[1])
    if len(args) != 1:
        sys.stderr.write("mylisp: expected a single program file\n")
        return 1
    return _run_file(args[0])


def _force_lf_streams() -> None:
    """Disable Windows CRLF translation on stdout/stderr (SPEC §6: LF only)."""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if isinstance(stream, io.TextIOWrapper):
            cast(io.TextIOWrapper, stream).reconfigure(newline="")


if __name__ == "__main__":
    _force_lf_streams()
    sys.exit(main())
