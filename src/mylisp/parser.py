"""S-expression parser. See SPEC §4.

Consumes the token stream produced by :mod:`mylisp.lexer` and returns a
list of top-level expressions in the unified AST/value representation
defined in :mod:`mylisp.ast`. ``'X`` is desugared to ``(quote X)`` here.
"""

from __future__ import annotations

from typing import cast

from . import MylispError
from .ast import EMPTY, Pair, Symbol, Value
from .lexer import Token, TokenKind


class ParseError(MylispError):
    def __init__(self, message: str, line: int, col: int) -> None:
        super().__init__(f"ParseError: {message} at line {line}, col {col}")
        self.message: str = message
        self.line: int = line
        self.col: int = col


def parse(tokens: list[Token]) -> list[Value]:
    """Parse a token stream into a list of top-level S-expressions."""
    result: list[Value] = []
    pos = 0
    while tokens[pos].kind != TokenKind.EOF:
        expr, pos = _parse_expr(tokens, pos)
        result.append(expr)
    return result


def _parse_expr(tokens: list[Token], pos: int) -> tuple[Value, int]:
    tok = tokens[pos]
    kind = tok.kind
    if kind == TokenKind.LPAREN:
        return _parse_list(tokens, pos + 1, tok.line, tok.col)
    if kind == TokenKind.RPAREN:
        raise ParseError("unexpected ')'", tok.line, tok.col)
    if kind == TokenKind.QUOTE:
        if tokens[pos + 1].kind == TokenKind.EOF:
            raise ParseError(
                "expected expression after quote", tok.line, tok.col
            )
        inner, next_pos = _parse_expr(tokens, pos + 1)
        quoted: Value = Pair(Symbol("quote"), Pair(inner, EMPTY))
        return quoted, next_pos
    if kind == TokenKind.INT:
        return cast(int, tok.value), pos + 1
    if kind == TokenKind.BOOL:
        return cast(bool, tok.value), pos + 1
    if kind == TokenKind.STRING:
        return cast(str, tok.value), pos + 1
    if kind == TokenKind.SYMBOL:
        return Symbol(cast(str, tok.value)), pos + 1
    raise ParseError(
        f"unexpected token {kind.name}", tok.line, tok.col
    )


def _parse_list(
    tokens: list[Token], pos: int, open_line: int, open_col: int
) -> tuple[Value, int]:
    elements: list[Value] = []
    while True:
        tok = tokens[pos]
        if tok.kind == TokenKind.RPAREN:
            result: Value = EMPTY
            for elem in reversed(elements):
                result = Pair(elem, result)
            return result, pos + 1
        if tok.kind == TokenKind.EOF:
            raise ParseError("unterminated list", open_line, open_col)
        elem, pos = _parse_expr(tokens, pos)
        elements.append(elem)
