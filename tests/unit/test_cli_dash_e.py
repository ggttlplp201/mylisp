"""Tests for the SPEC §1.3 ``-e`` CLI mode.

``./mylisp -e "<expr>"`` evaluates exactly one expression. Zero or multiple
top-level forms must be rejected without producing any stdout output.
"""

from __future__ import annotations

import pytest

from mylisp.__main__ import main


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
