import pytest

from django_shield.exceptions import ExpressionSyntaxError
from django_shield.expressions.lexer import ShieldLexer


class TestLexerKeywords:
    def test_and_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("and"))
        assert len(tokens) == 1
        assert tokens[0].type == "AND"

    def test_or_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("or"))
        assert len(tokens) == 1
        assert tokens[0].type == "OR"

    def test_not_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("not"))
        assert len(tokens) == 1
        assert tokens[0].type == "NOT"

    def test_in_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("in"))
        assert len(tokens) == 1
        assert tokens[0].type == "IN"

    def test_true_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("true"))
        assert len(tokens) == 1
        assert tokens[0].type == "TRUE"

    def test_true_capitalized(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("True"))
        assert len(tokens) == 1
        assert tokens[0].type == "TRUE"

    def test_false_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("false"))
        assert len(tokens) == 1
        assert tokens[0].type == "FALSE"

    def test_false_capitalized(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("False"))
        assert len(tokens) == 1
        assert tokens[0].type == "FALSE"

    def test_null_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("null"))
        assert len(tokens) == 1
        assert tokens[0].type == "NULL"

    def test_none_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("None"))
        assert len(tokens) == 1
        assert tokens[0].type == "NULL"

    def test_obj_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("obj"))
        assert len(tokens) == 1
        assert tokens[0].type == "OBJ"

    def test_user_keyword(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("user"))
        assert len(tokens) == 1
        assert tokens[0].type == "USER"


class TestLexerOperators:
    def test_eq_operator(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("=="))
        assert len(tokens) == 1
        assert tokens[0].type == "EQ"

    def test_ne_operator(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("!="))
        assert len(tokens) == 1
        assert tokens[0].type == "NE"

    def test_gt_operator(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize(">"))
        assert len(tokens) == 1
        assert tokens[0].type == "GT"

    def test_lt_operator(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("<"))
        assert len(tokens) == 1
        assert tokens[0].type == "LT"

    def test_ge_operator(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize(">="))
        assert len(tokens) == 1
        assert tokens[0].type == "GE"

    def test_le_operator(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("<="))
        assert len(tokens) == 1
        assert tokens[0].type == "LE"


class TestLexerValues:
    def test_string_simple(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize('"hello"'))
        assert len(tokens) == 1
        assert tokens[0].type == "STRING"
        assert tokens[0].value == "hello"

    def test_string_with_spaces(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize('"hello world"'))
        assert len(tokens) == 1
        assert tokens[0].type == "STRING"
        assert tokens[0].value == "hello world"

    def test_integer(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("42"))
        assert len(tokens) == 1
        assert tokens[0].type == "NUMBER"
        assert tokens[0].value == 42

    def test_negative_integer(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("-42"))
        assert len(tokens) == 1
        assert tokens[0].type == "NUMBER"
        assert tokens[0].value == -42

    def test_float(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("3.14"))
        assert len(tokens) == 1
        assert tokens[0].type == "NUMBER"
        assert tokens[0].value == 3.14

    def test_negative_float(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("-3.14"))
        assert len(tokens) == 1
        assert tokens[0].type == "NUMBER"
        assert tokens[0].value == -3.14

    def test_name(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("is_admin"))
        assert len(tokens) == 1
        assert tokens[0].type == "NAME"
        assert tokens[0].value == "is_admin"


class TestLexerSymbols:
    def test_dot(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("."))
        assert len(tokens) == 1
        assert tokens[0].type == "DOT"

    def test_lparen(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("("))
        assert len(tokens) == 1
        assert tokens[0].type == "LPAREN"

    def test_rparen(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize(")"))
        assert len(tokens) == 1
        assert tokens[0].type == "RPAREN"

    def test_lbracket(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("["))
        assert len(tokens) == 1
        assert tokens[0].type == "LBRACKET"

    def test_rbracket(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("]"))
        assert len(tokens) == 1
        assert tokens[0].type == "RBRACKET"

    def test_comma(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize(","))
        assert len(tokens) == 1
        assert tokens[0].type == "COMMA"


class TestLexerWhitespace:
    def test_ignores_spaces(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("a   b"))
        assert len(tokens) == 2
        assert tokens[0].value == "a"
        assert tokens[1].value == "b"

    def test_ignores_tabs(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize("a\tb"))
        assert len(tokens) == 2


class TestLexerErrors:
    def test_invalid_character(self):
        lexer = ShieldLexer()
        lexer.text = "@"
        with pytest.raises(ExpressionSyntaxError) as exc_info:
            list(lexer.tokenize("@"))
        assert "Invalid character '@'" in str(exc_info.value)


class TestLexerComplex:
    def test_complex_expression(self):
        lexer = ShieldLexer()
        tokens = list(lexer.tokenize('obj.status == "draft" and user.is_staff'))
        types = [t.type for t in tokens]
        assert types == [
            "OBJ",
            "DOT",
            "NAME",
            "EQ",
            "STRING",
            "AND",
            "USER",
            "DOT",
            "NAME",
        ]
