"""Interactive REPL for mylisp. See SPEC §11.

The function :func:`run_repl` is the SPEC §11.5 programmatic entry point:
when ``inputs is None`` it reads ``sys.stdin`` and integrates ``readline``;
when ``inputs`` is supplied it pulls lines from that iterable (test mode)
and skips ``readline`` entirely. Either path produces identical evaluation
behaviour — multiline accumulation, directives, and error recovery all live
in the shared loop body below.
"""

from __future__ import annotations

import atexit
import sys
from pathlib import Path
from typing import Iterable, Iterator, TextIO

from . import MylispError
from .ast import EMPTY, Pair, Symbol, Unspecified, Value
from .env import Env
from .evaluator import evaluate
from .lexer import LexError, tokenize
from .parser import ParseError, parse
from .printer import write as write_value

PRIMARY_PROMPT = "mylisp> "
CONTINUE_PROMPT = "...... "
HISTORY_FILENAME = ".mylisp_history"
HISTORY_LIMIT = 1000

HELP_TEXT = (
    ":quit (also :q, :exit) -- exit the REPL\n"
    ":help                  -- show this help\n"
    ":load <path>           -- read and evaluate the file at <path>\n"
    ":env                   -- list global bindings, one per line\n"
)

_INCOMPLETE_PARSE_MESSAGES: frozenset[str] = frozenset(
    {"unterminated list", "expected expression after quote"}
)
_INCOMPLETE_LEX_MESSAGES: frozenset[str] = frozenset({"unterminated string literal"})


def _is_incomplete_input(exc: MylispError) -> bool:
    """True iff ``exc`` reflects a buffer that may parse once more input arrives."""
    if isinstance(exc, ParseError):
        return exc.message in _INCOMPLETE_PARSE_MESSAGES
    if isinstance(exc, LexError):
        return exc.message in _INCOMPLETE_LEX_MESSAGES
    return False


def _try_setup_readline() -> bool:
    """Import ``readline`` and wire history. Returns True iff it succeeded."""
    try:
        import readline
    except ImportError:
        return False
    history_file = Path.home() / HISTORY_FILENAME
    try:
        history_file.touch(exist_ok=True)
        readline.read_history_file(str(history_file))
    except OSError:
        pass
    readline.set_history_length(HISTORY_LIMIT)
    atexit.register(_write_history_file, str(history_file))
    return True


def _write_history_file(path: str) -> None:
    try:
        import readline
    except ImportError:
        return
    try:
        readline.write_history_file(path)
    except OSError:
        pass


def _handle_directive(line: str, env: Env, out: TextIO, err: TextIO) -> bool:
    """Run a REPL directive (SPEC §11.3). Returns True iff the REPL should exit."""
    body = line.lstrip()[1:]
    head = body.split(None, 1)
    name = head[0] if head else ""
    rest = head[1] if len(head) > 1 else ""

    if name in {"quit", "q", "exit"}:
        return True
    if name == "help":
        out.write(HELP_TEXT)
        return False
    if name == "load":
        path = rest.rstrip()
        if not path:
            err.write("RuntimeError: load failed: missing path\n")
            return False
        expr: Value = Pair(Symbol("load"), Pair(path, EMPTY))
        try:
            evaluate(expr, env)
        except MylispError as exc:
            err.write(str(exc) + "\n")
        return False
    if name == "env":
        for binding in sorted(env.names()):
            out.write(binding + "\n")
        return False
    err.write(f"REPL: unknown directive :{name}. Try :help.\n")
    return False


def run_repl(
    inputs: Iterable[str] | None = None,
    out: TextIO | None = None,
    err: TextIO | None = None,
) -> int:
    """Drive the SPEC §11 REPL.

    ``inputs is None`` engages stdin/readline mode (the CLI no-args path).
    Passing an iterable runs the same loop against synthetic input — the
    test seam called out in SPEC §11.5.
    """
    from .__main__ import _make_global_env

    stream_out: TextIO = sys.stdout if out is None else out
    stream_err: TextIO = sys.stderr if err is None else err

    try:
        env = _make_global_env()
    except MylispError as exc:
        stream_err.write(str(exc) + "\n")
        return 1

    iterator: Iterator[str] | None = None
    if inputs is None:
        _try_setup_readline()
    else:
        iterator = iter(inputs)

    buffer = ""
    while True:
        prompt = PRIMARY_PROMPT if not buffer else CONTINUE_PROMPT
        try:
            if iterator is None:
                line = input(prompt)
            else:
                try:
                    line = next(iterator)
                except StopIteration:
                    return 0
        except EOFError:
            if iterator is None:
                stream_out.write("\n")
            if not buffer:
                return 0
            buffer = ""
            continue
        except KeyboardInterrupt:
            if iterator is None:
                stream_out.write("\n")
            buffer = ""
            continue

        if not buffer and line.lstrip().startswith(":"):
            if _handle_directive(line, env, stream_out, stream_err):
                return 0
            continue

        candidate = buffer + line + "\n"
        try:
            tokens = tokenize(candidate)
            exprs = parse(tokens)
        except MylispError as exc:
            if _is_incomplete_input(exc):
                buffer = candidate
                continue
            stream_err.write(str(exc) + "\n")
            buffer = ""
            continue

        buffer = ""
        try:
            for expr in exprs:
                result = evaluate(expr, env)
                if not isinstance(result, Unspecified):
                    stream_out.write(write_value(result) + "\n")
        except MylispError as exc:
            stream_err.write(str(exc) + "\n")
