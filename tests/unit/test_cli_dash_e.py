"""Tests for the SPEC §1.3 ``-e`` CLI mode.

``./mylisp -e "<expr>"`` evaluates exactly one expression. Zero or multiple
top-level forms must be rejected without producing any stdout output.
"""

from __future__ import annotations

import pytest

from mylisp import __main__ as cli_main
from mylisp.__main__ import PreludeLoadError, main


def test_dash_e_single_expression_prints_write_form(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["-e", "(+ 1 2)"])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out == "3\n"
    assert captured.err == ""


def test_dash_e_rejects_empty_input(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["-e", ""])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert captured.err == "mylisp: -e requires exactly one expression\n"


def test_dash_e_rejects_whitespace_only_input(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["-e", "   \n\t"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert captured.err == "mylisp: -e requires exactly one expression\n"


def test_dash_e_rejects_comment_only_input(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["-e", "; just a comment"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert captured.err == "mylisp: -e requires exactly one expression\n"


def test_dash_e_rejects_multiple_expressions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["-e", "1 2"])
    captured = capsys.readouterr()
    assert rc == 1
    # Must not print the first expression before detecting the overflow.
    assert captured.out == ""
    assert captured.err == "mylisp: -e requires exactly one expression\n"


def test_dash_e_rejects_multiple_compound_expressions(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["-e", "(+ 1 2) (+ 3 4)"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert captured.err == "mylisp: -e requires exactly one expression\n"


def test_dash_e_prelude_failure_takes_precedence_over_empty_input(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SPEC §5.11: the prelude must be fully evaluated before a `-e` expression
    is parsed. A prelude-load failure must therefore surface before any
    rejection of zero- or multi-expression `-e` payloads.
    """

    def _boom(_env: object) -> None:
        raise PreludeLoadError("synthetic prelude failure")

    monkeypatch.setattr(cli_main, "_load_prelude", _boom)
    rc = main(["-e", ""])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert (
        captured.err
        == "RuntimeError: prelude load failed: synthetic prelude failure\n"
    )


def test_dash_e_prelude_failure_takes_precedence_over_lex_error(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A LexError in the `-e` payload must not be reported when the prelude
    cannot load — the env is built first, so the prelude error wins.
    """

    def _boom(_env: object) -> None:
        raise PreludeLoadError("synthetic prelude failure")

    monkeypatch.setattr(cli_main, "_load_prelude", _boom)
    rc = main(["-e", '"unterminated'])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert (
        captured.err
        == "RuntimeError: prelude load failed: synthetic prelude failure\n"
    )


def test_dash_e_prelude_failure_takes_precedence_over_multi_expression(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multi-expression `-e` input must not be reported when the prelude
    cannot load — bootstrap order (§5.11) puts the prelude before the parse.
    """

    def _boom(_env: object) -> None:
        raise PreludeLoadError("synthetic prelude failure")

    monkeypatch.setattr(cli_main, "_load_prelude", _boom)
    rc = main(["-e", "1 2"])
    captured = capsys.readouterr()
    assert rc == 1
    assert captured.out == ""
    assert (
        captured.err
        == "RuntimeError: prelude load failed: synthetic prelude failure\n"
    )
