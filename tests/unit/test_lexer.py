import pytest

from mylisp.lexer import LexError, Token, TokenKind, tokenize


def test_empty_source():
    assert tokenize("") == [Token(TokenKind.EOF, None, 1, 1)]


def test_whitespace_only():
    toks = tokenize("   \t\n  ")
    assert [t.kind for t in toks] == [TokenKind.EOF]


def test_parens():
    toks = tokenize("()")
    assert [t.kind for t in toks] == [
        TokenKind.LPAREN,
        TokenKind.RPAREN,
        TokenKind.EOF,
    ]
    assert toks[0].col == 1 and toks[1].col == 2


def test_integer_positive():
    assert tokenize("42")[0] == Token(TokenKind.INT, 42, 1, 1)


def test_integer_negative():
    assert tokenize("-7")[0] == Token(TokenKind.INT, -7, 1, 1)


def test_integer_zero():
    assert tokenize("0")[0] == Token(TokenKind.INT, 0, 1, 1)


def test_plus_three_is_symbol_not_integer():
    # Per SPEC §4.1: "+3" is NOT a valid integer; it is a symbol.
    assert tokenize("+3")[0] == Token(TokenKind.SYMBOL, "+3", 1, 1)


def test_minus_alone_is_symbol():
    assert tokenize("-")[0] == Token(TokenKind.SYMBOL, "-", 1, 1)


def test_boolean_true():
    assert tokenize("#t")[0] == Token(TokenKind.BOOL, True, 1, 1)


def test_boolean_false():
    assert tokenize("#f")[0] == Token(TokenKind.BOOL, False, 1, 1)


def test_string_simple():
    assert tokenize('"hello"')[0] == Token(TokenKind.STRING, "hello", 1, 1)


def test_string_empty():
    assert tokenize('""')[0] == Token(TokenKind.STRING, "", 1, 1)


def test_string_escapes():
    src = r'"a\nb\tc\"d\\e"'
    assert tokenize(src)[0].value == 'a\nb\tc"d\\e'


def test_arithmetic_symbols():
    for sym in ("+", "-", "*", "/", "<", ">", "=", "<=", ">="):
        toks = tokenize(sym)
        assert toks[0].kind == TokenKind.SYMBOL
        assert toks[0].value == sym


def test_alphanumeric_symbol():
    assert tokenize("foo-bar?")[0] == Token(TokenKind.SYMBOL, "foo-bar?", 1, 1)


def test_symbol_with_digit_in_middle():
    assert tokenize("x1y2")[0] == Token(TokenKind.SYMBOL, "x1y2", 1, 1)


def test_quote_sugar():
    toks = tokenize("'x")
    assert toks[0].kind == TokenKind.QUOTE
    assert toks[1] == Token(TokenKind.SYMBOL, "x", 1, 2)


def test_comment_to_eol():
    toks = tokenize("; ignored\n42")
    assert toks[0] == Token(TokenKind.INT, 42, 2, 1)
    assert toks[1].kind == TokenKind.EOF


def test_multiple_tokens():
    toks = tokenize("(+ 1 2)")
    assert [t.kind for t in toks] == [
        TokenKind.LPAREN,
        TokenKind.SYMBOL,
        TokenKind.INT,
        TokenKind.INT,
        TokenKind.RPAREN,
        TokenKind.EOF,
    ]
    assert [t.value for t in toks] == [None, "+", 1, 2, None, None]


def test_line_col_tracking_across_newline():
    toks = tokenize("a\n  b")
    assert toks[0] == Token(TokenKind.SYMBOL, "a", 1, 1)
    assert toks[1] == Token(TokenKind.SYMBOL, "b", 2, 3)


def test_lex_error_invalid_string_escape():
    with pytest.raises(LexError) as exc:
        tokenize(r'"\x"')
    assert "invalid string escape" in exc.value.message
    assert exc.value.line == 1


def test_lex_error_unterminated_string():
    with pytest.raises(LexError) as exc:
        tokenize('"abc')
    assert "unterminated" in exc.value.message
    assert exc.value.line == 1
    assert exc.value.col == 1


def test_lex_error_unknown_hash():
    with pytest.raises(LexError) as exc:
        tokenize("#z")
    assert "unknown # token" in exc.value.message


def test_lex_error_message_format():
    with pytest.raises(LexError) as exc:
        tokenize("\n  #q")
    msg = str(exc.value)
    assert msg.startswith("LexError:")
    assert "line 2" in msg
    assert "col 3" in msg


def test_lex_error_invalid_atom_starting_with_digit():
    # "1abc" is neither a valid integer nor a valid symbol.
    with pytest.raises(LexError):
        tokenize("1abc")


def test_lex_error_boolean_followed_by_symbol_char():
    with pytest.raises(LexError):
        tokenize("#tx")


def test_string_preserves_unescaped_newline_and_advances_line():
    toks = tokenize('"a\nb" 1')
    assert toks[0] == Token(TokenKind.STRING, "a\nb", 1, 1)
    # After the multi-line string, the integer is on line 2.
    assert toks[1].line == 2
