"""Tests for the SPEC §11 REPL.

Drives :func:`mylisp.repl.run_repl` in test mode (synthetic ``inputs``) so
the loop runs deterministically without touching stdin or ``readline``.
"""

from __future__ import annotations

import builtins as builtin_module
import io
from pathlib import Path

import pytest

from mylisp.repl import HELP_TEXT, _try_setup_readline, run_repl


def _drive(lines: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    rc = run_repl(inputs=lines, out=out, err=err)
    return rc, out.getvalue(), err.getvalue()


def test_basic_expression_prints_in_write_form() -> None:
    rc, out, err = _drive(["(+ 1 2)"])
    assert rc == 0
    assert out == "3\n"
    assert err == ""


def test_multiline_accumulation_across_two_lines() -> None:
    rc, out, err = _drive(["(+ 1", " 2 3)"])
    assert rc == 0
    assert out == "6\n"
    assert err == ""


def test_multiline_with_unterminated_string() -> None:
    # The accumulator joins lines with '\n', so the literal contains
    # 'hello\n world' = 12 chars; this exercises the lex-error continuation path.
    rc, out, err = _drive(['(string-length "hello', ' world")'])
    assert rc == 0
    assert out == "12\n"
    assert err == ""


def test_multiline_carries_quote_target_across_lines() -> None:
    rc, out, err = _drive(["'", "(1 2)"])
    assert rc == 0
    assert out == "(1 2)\n"
    assert err == ""


def test_multiple_expressions_on_one_line_print_in_order() -> None:
    rc, out, err = _drive(["1 2 3"])
    assert rc == 0
    assert out == "1\n2\n3\n"


def test_define_does_not_print_then_binding_is_visible() -> None:
    rc, out, err = _drive(["(define x 7)", "x"])
    assert rc == 0
    assert out == "7\n"
    assert err == ""


def test_quit_directive_returns_zero() -> None:
    # After :quit the iterator never advances to the next line.
    rc, out, err = _drive([":quit", "(+ 1 2)"])
    assert rc == 0
    assert out == ""
    assert err == ""


def test_quit_aliases() -> None:
    for alias in (":q", ":exit"):
        rc, out, err = _drive([alias, "(+ 1 2)"])
        assert rc == 0, alias
        assert out == "", alias


def test_help_directive_lists_every_required_name() -> None:
    rc, out, err = _drive([":help"])
    assert rc == 0
    # SPEC §11.3 acceptance: every directive name is present in :help output.
    for required in (":quit", ":help", ":load", ":env"):
        assert required in out
    assert err == ""


def test_unknown_directive_reports_and_continues() -> None:
    rc, out, err = _drive([":bogus", "1"])
    assert rc == 0
    assert out == "1\n"
    assert err == "REPL: unknown directive :bogus. Try :help.\n"


def test_env_directive_prints_global_bindings_sorted() -> None:
    rc, out, err = _drive([":env"])
    assert rc == 0
    assert err == ""
    lines = out.splitlines()
    # Sorted, no duplicates.
    assert lines == sorted(lines)
    assert len(lines) == len(set(lines))
    # Builtins and prelude bindings are both visible.
    expected_subset = {"+", "car", "cons", "load", "map", "filter", "append"}
    assert expected_subset.issubset(set(lines))


def test_env_reflects_user_defines() -> None:
    rc, out, err = _drive(["(define my-name 1)", ":env"])
    assert rc == 0
    assert "my-name" in out.splitlines()


def test_load_directive_evaluates_file(tmp_path: Path) -> None:
    helper = tmp_path / "helper.lisp"
    helper.write_text("(define answer 42)\n", encoding="utf-8")
    rc, out, err = _drive([f":load {helper}", "answer"])
    assert rc == 0, err
    assert out == "42\n"
    assert err == ""


def test_load_directive_missing_path_reports_error() -> None:
    rc, out, err = _drive([":load"])
    assert rc == 0
    assert "load failed" in err


def test_load_directive_missing_file_reports_error(tmp_path: Path) -> None:
    missing = tmp_path / "nope.lisp"
    rc, out, err = _drive([f":load {missing}", "1"])
    assert rc == 0
    assert out == "1\n"
    assert err.startswith("RuntimeError: load failed: cannot read")


def test_parse_error_recovery() -> None:
    rc, out, err = _drive(["))", "(+ 1 2)"])
    assert rc == 0
    assert out == "3\n"
    assert err.startswith("ParseError:")


def test_lex_error_recovery() -> None:
    rc, out, err = _drive(['"bad\\x"', "(+ 1 2)"])
    assert rc == 0
    assert out == "3\n"
    assert err.startswith("LexError:")


def test_runtime_error_recovery() -> None:
    rc, out, err = _drive(["(/ 1 0)", "(+ 1 2)"])
    assert rc == 0
    assert out == "3\n"
    assert err == "RuntimeError: division by zero\n"


def test_unbound_symbol_recovery() -> None:
    rc, out, err = _drive(["undefined-name", "42"])
    assert rc == 0
    assert out == "42\n"
    assert err == "RuntimeError: unbound symbol: undefined-name\n"


def test_iterator_exhaustion_returns_zero_without_extra_output() -> None:
    rc, out, err = _drive([])
    assert rc == 0
    assert out == ""
    assert err == ""


def test_blank_lines_are_ignored() -> None:
    rc, out, err = _drive(["", "   ", "1"])
    assert rc == 0
    assert out == "1\n"
    assert err == ""


def test_try_setup_readline_returns_false_when_import_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SPEC §11.2: REPL must catch ImportError silently."""
    real_import = builtin_module.__import__

    def fake_import(
        name: str, *args: object, **kwargs: object
    ) -> object:
        if name == "readline":
            raise ImportError("simulated absence of readline")
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtin_module, "__import__", fake_import)
    assert _try_setup_readline() is False


def test_help_text_constant_matches_help_directive_output() -> None:
    rc, out, err = _drive([":help"])
    assert rc == 0
    assert out == HELP_TEXT


def test_primitive_io_is_captured_by_injected_out_stream(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SPEC §11.5: display/write/newline must honour the injected ``out`` stream.

    Regression for iteration 14 REVIEW: the I/O builtins used to write
    directly to ``sys.stdout``, so REPL test fixtures could not observe
    side-effecting output.
    """
    rc, out, err = _drive(
        [
            '(display "hi")',
            "(newline)",
            '(write "bye")',
            "(newline)",
        ]
    )
    assert rc == 0
    assert err == ""
    assert out == 'hi\n"bye"\n'
    # Real stdout/stderr must stay empty: the primitives no longer leak past ``out``.
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
