"""Tokenizer for mylisp source. See SPEC §4."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from . import MylispError


class TokenKind(Enum):
    LPAREN = auto()
    RPAREN = auto()
    QUOTE = auto()
    INT = auto()
    BOOL = auto()
    STRING = auto()
    SYMBOL = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: int | bool | str | None
    line: int
    col: int


class LexError(MylispError):
    def __init__(self, message: str, line: int, col: int) -> None:
        super().__init__(f"LexError: {message} at line {line}, col {col}")
        self.message: str = message
        self.line: int = line
        self.col: int = col


_SYMBOL_START_CHARS: frozenset[str] = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/<>=!?_"
)
_SYMBOL_CONT_CHARS: frozenset[str] = _SYMBOL_START_CHARS | frozenset("0123456789")
_ATOM_TERMINATORS: frozenset[str] = frozenset(" \t\r\n();'\"")
_STRING_ESCAPES: dict[str, str] = {"\\": "\\", '"': '"', "n": "\n", "t": "\t"}


def _is_integer(atom: str) -> bool:
    if not atom:
        return False
    body = atom[1:] if atom[0] == "-" else atom
    return len(body) > 0 and all(c.isdigit() for c in body)


def _is_symbol(atom: str) -> bool:
    if not atom:
        return False
    if atom[0] not in _SYMBOL_START_CHARS:
        return False
    return all(c in _SYMBOL_CONT_CHARS for c in atom[1:])


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    line = 1
    col = 1
    n = len(source)

    while i < n:
        ch = source[i]
        if ch == " " or ch == "\t" or ch == "\r":
            i += 1
            col += 1
        elif ch == "\n":
            i += 1
            line += 1
            col = 1
        elif ch == ";":
            while i < n and source[i] != "\n":
                i += 1
                col += 1
        elif ch == "(":
            tokens.append(Token(TokenKind.LPAREN, None, line, col))
            i += 1
            col += 1
        elif ch == ")":
            tokens.append(Token(TokenKind.RPAREN, None, line, col))
            i += 1
            col += 1
        elif ch == "'":
            tokens.append(Token(TokenKind.QUOTE, None, line, col))
            i += 1
            col += 1
        elif ch == '"':
            start_line, start_col = line, col
            i += 1
            col += 1
            buf: list[str] = []
            terminated = False
            while i < n:
                c = source[i]
                if c == '"':
                    terminated = True
                    i += 1
                    col += 1
                    break
                if c == "\\":
                    if i + 1 >= n:
                        raise LexError(
                            "unterminated string literal", start_line, start_col
                        )
                    esc = source[i + 1]
                    if esc not in _STRING_ESCAPES:
                        raise LexError(f"invalid string escape \\{esc}", line, col)
                    buf.append(_STRING_ESCAPES[esc])
                    i += 2
                    col += 2
                elif c == "\n":
                    buf.append(c)
                    i += 1
                    line += 1
                    col = 1
                else:
                    buf.append(c)
                    i += 1
                    col += 1
            if not terminated:
                raise LexError("unterminated string literal", start_line, start_col)
            tokens.append(
                Token(TokenKind.STRING, "".join(buf), start_line, start_col)
            )
        elif ch == "#":
            start_line, start_col = line, col
            if i + 1 >= n:
                raise LexError(
                    "unexpected end of input after '#'", start_line, start_col
                )
            nxt = source[i + 1]
            if nxt != "t" and nxt != "f":
                raise LexError(f"unknown # token: #{nxt}", start_line, start_col)
            if i + 2 < n and source[i + 2] in _SYMBOL_CONT_CHARS:
                bad = source[i : i + 3]
                raise LexError(f"unknown # token: {bad}", start_line, start_col)
            tokens.append(Token(TokenKind.BOOL, nxt == "t", start_line, start_col))
            i += 2
            col += 2
        else:
            start_line, start_col = line, col
            atom_start = i
            while i < n and source[i] not in _ATOM_TERMINATORS:
                i += 1
                col += 1
            atom = source[atom_start:i]
            if _is_integer(atom):
                tokens.append(
                    Token(TokenKind.INT, int(atom), start_line, start_col)
                )
            elif _is_symbol(atom):
                tokens.append(Token(TokenKind.SYMBOL, atom, start_line, start_col))
            else:
                raise LexError(f"invalid token {atom!r}", start_line, start_col)

    tokens.append(Token(TokenKind.EOF, None, line, col))
    return tokens
