import pytest

from mylisp.ast import EMPTY, Pair, Symbol
from mylisp.lexer import tokenize
from mylisp.parser import ParseError, parse


def _parse(src: str):
    return parse(tokenize(src))


def test_parse_empty_source_yields_no_expressions():
    assert _parse("") == []


def test_parse_integer_literal():
    assert _parse("42") == [42]


def test_parse_negative_integer_literal():
    assert _parse("-7") == [-7]


def test_parse_boolean_literals():
    result = _parse("#t #f")
    # Use a strict identity-and-type check so bool/int aren't conflated.
    assert result == [True, False]
    assert type(result[0]) is bool
    assert type(result[1]) is bool


def test_parse_string_literal():
    assert _parse('"hello"') == ["hello"]


def test_parse_symbol():
    assert _parse("foo") == [Symbol("foo")]


def test_parse_empty_list():
    assert _parse("()") == [EMPTY]


def test_parse_nested_application():
    # (+ 1 2) -> Pair(+, Pair(1, Pair(2, EMPTY)))
    expected = Pair(Symbol("+"), Pair(1, Pair(2, EMPTY)))
    assert _parse("(+ 1 2)") == [expected]


def test_parse_nested_lists():
    # (a (b c)) -> Pair(a, Pair(Pair(b, Pair(c, ())), ()))
    expected = Pair(
        Symbol("a"),
        Pair(Pair(Symbol("b"), Pair(Symbol("c"), EMPTY)), EMPTY),
    )
    assert _parse("(a (b c))") == [expected]


def test_parse_quote_sugar_on_symbol():
    # 'x -> (quote x)
    expected = Pair(Symbol("quote"), Pair(Symbol("x"), EMPTY))
    assert _parse("'x") == [expected]


def test_parse_quote_sugar_on_list():
    # '(1 2) -> (quote (1 2))
    inner = Pair(1, Pair(2, EMPTY))
    expected = Pair(Symbol("quote"), Pair(inner, EMPTY))
    assert _parse("'(1 2)") == [expected]


def test_parse_nested_quote():
    # ''x -> (quote (quote x))
    inner = Pair(Symbol("quote"), Pair(Symbol("x"), EMPTY))
    expected = Pair(Symbol("quote"), Pair(inner, EMPTY))
    assert _parse("''x") == [expected]


def test_parse_multiple_top_level_expressions():
    assert _parse("1 2 3") == [1, 2, 3]
    result = _parse("(define x 1) (+ x 2)")
    assert len(result) == 2
    assert result[0] == Pair(
        Symbol("define"), Pair(Symbol("x"), Pair(1, EMPTY))
    )


def test_parse_error_on_unmatched_close_paren():
    with pytest.raises(ParseError) as exc:
        _parse(")")
    assert "unexpected ')'" in exc.value.message
    assert exc.value.line == 1
    assert exc.value.col == 1


def test_parse_error_on_unterminated_list_reports_open_paren():
    with pytest.raises(ParseError) as exc:
        _parse("(1 2 3")
    assert "unterminated list" in exc.value.message
    # The location should point at the *opening* paren, not EOF.
    assert exc.value.line == 1
    assert exc.value.col == 1


def test_parse_error_unterminated_nested_list_points_at_inner_open():
    with pytest.raises(ParseError) as exc:
        _parse("(a (b c)")
    assert "unterminated list" in exc.value.message
    # Outer ( is at col 1; that's the one that's still open at EOF.
    assert exc.value.col == 1


def test_parse_error_quote_at_eof():
    with pytest.raises(ParseError) as exc:
        _parse("'")
    assert "expected expression after quote" in exc.value.message


def test_parse_error_message_format():
    with pytest.raises(ParseError) as exc:
        _parse("\n  )")
    msg = str(exc.value)
    assert msg.startswith("ParseError:")
    assert "line 2" in msg
    assert "col 3" in msg


def test_parse_quote_inside_list():
    # (list 'a 'b) -> (list (quote a) (quote b))
    expected = Pair(
        Symbol("list"),
        Pair(
            Pair(Symbol("quote"), Pair(Symbol("a"), EMPTY)),
            Pair(
                Pair(Symbol("quote"), Pair(Symbol("b"), EMPTY)),
                EMPTY,
            ),
        ),
    )
    assert _parse("(list 'a 'b)") == [expected]


def test_parse_preserves_string_value_through_pair():
    # ("hi") parses to Pair("hi", EMPTY)
    assert _parse('("hi")') == [Pair("hi", EMPTY)]
