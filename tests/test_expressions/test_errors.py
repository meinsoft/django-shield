import pytest

from django_shield.exceptions import ExpressionSyntaxError
from django_shield.expressions.parser import parse_expression


class TestExpressionSyntaxError:
    def test_error_shows_expression(self):
        try:
            parse_expression("obj.status == == 'draft'")
        except ExpressionSyntaxError as e:
            assert "obj.status == == 'draft'" in str(e)

    def test_unclosed_parenthesis_error(self):
        with pytest.raises(ExpressionSyntaxError) as exc_info:
            parse_expression("(is_admin")
        assert "Unexpected end of expression" in str(
            exc_info.value
        ) or "Unexpected" in str(exc_info.value)

    def test_unclosed_bracket_error(self):
        with pytest.raises(ExpressionSyntaxError) as exc_info:
            parse_expression('obj.status in ["draft"')
        assert "Unexpected" in str(exc_info.value)

    def test_invalid_character_error(self):
        with pytest.raises(ExpressionSyntaxError) as exc_info:
            parse_expression("@invalid")
        assert "Invalid character" in str(exc_info.value)

    def test_double_operator_error(self):
        with pytest.raises(ExpressionSyntaxError):
            parse_expression("a and and b")

    def test_trailing_operator_error(self):
        with pytest.raises(ExpressionSyntaxError):
            parse_expression("a and")
