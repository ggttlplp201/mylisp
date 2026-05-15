"""Regression test for SPEC §5.12.1: closure-contained relative ``load``.

A closure defined in file A whose body calls ``(load "x")`` must resolve
``x`` relative to A's directory, even when the closure is invoked from
elsewhere (file B, the REPL, or the top level of a different program).
Previously the loader resolved against whichever file was active at call
time, which violated the SPEC.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from mylisp.__main__ import _run_file


def _write(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


def test_closure_load_resolves_against_closure_source(tmp_path: Path) -> None:
    """A closure from sub/helper.lisp must resolve (load "z.lisp") in sub/."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write(sub / "helper.lisp", "(define (use-z) (load \"z.lisp\"))\n")
    _write(sub / "z.lisp", "(define z-loaded 99)\n")
    _write(
        tmp_path / "main.lisp",
        "(load \"sub/helper.lisp\")\n(use-z)\nz-loaded\n",
    )

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        rc = _run_file(str(tmp_path / "main.lisp"))
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    assert rc == 0
    assert out.strip().splitlines()[-1] == "99"
