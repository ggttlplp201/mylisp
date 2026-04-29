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
from typing import Optional, cast

from . import MylispError
from .ast import Unspecified
from .builtins import builtin_bindings
from .env import Env
from .lexer import tokenize
from .parser import parse
from .evaluator import evaluate
from .printer import write


def _make_global_env() -> Env:
    return Env(builtin_bindings())


def _run_program(source: str, env: Env) -> None:
    """Tokenize, parse, and evaluate ``source``; print top-level results."""
    tokens = tokenize(source)
    exprs = parse(tokens)
    for expr in exprs:
        result = evaluate(expr, env)
        if not isinstance(result, Unspecified):
            sys.stdout.write(write(result) + "\n")


def _run_file(path: str) -> int:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            source = fh.read()
    except OSError as exc:
        sys.stderr.write(f"mylisp: cannot read {path}: {exc}\n")
        return 1
    env = _make_global_env()
    try:
        _run_program(source, env)
    except MylispError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    return 0


def _run_expr(source: str) -> int:
    env = _make_global_env()
    try:
        _run_program(source, env)
    except MylispError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 1
    return 0


def _run_repl() -> int:
    env = _make_global_env()
    while True:
        try:
            line = input("mylisp> ")
        except EOFError:
            sys.stdout.write("\n")
            return 0
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            continue
        if not line.strip():
            continue
        try:
            tokens = tokenize(line)
            exprs = parse(tokens)
            for expr in exprs:
                result = evaluate(expr, env)
                if not isinstance(result, Unspecified):
                    sys.stdout.write(write(result) + "\n")
        except MylispError as exc:
            sys.stderr.write(str(exc) + "\n")


def main(argv: Optional[list[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        return _run_repl()
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
