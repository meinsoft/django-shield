import pytest

from django_shield.exceptions import ExpressionSyntaxError
from django_shield.expressions.ast import (
    AndExpr,
    Compare,
    InExpr,
    ListExpr,
    Literal,
    NotExpr,
    ObjAttr,
    OrExpr,
    RuleRef,
    UserAttr,
    UserRef,
)
from django_shield.expressions.parser import parse_expression


class TestParserRuleRef:
    def test_simple_rule_ref(self):
        result = parse_expression("is_admin")
        assert result == RuleRef("is_admin")

    def test_rule_ref_with_underscore(self):
        result = parse_expression("can_edit_post")
        assert result == RuleRef("can_edit_post")


class TestParserObjAttr:
    def test_single_attribute(self):
        result = parse_expression("obj.status")
        assert result == ObjAttr(["status"])

    def test_nested_attribute(self):
        result = parse_expression("obj.author.name")
        assert result == ObjAttr(["author", "name"])

    def test_deeply_nested_attribute(self):
        result = parse_expression("obj.a.b.c.d")
        assert result == ObjAttr(["a", "b", "c", "d"])


class TestParserUserAttr:
    def test_single_attribute(self):
        result = parse_expression("user.is_staff")
        assert result == UserAttr(["is_staff"])

    def test_nested_attribute(self):
        result = parse_expression("user.profile.name")
        assert result == UserAttr(["profile", "name"])


class TestParserUserRef:
    def test_user_alone(self):
        result = parse_expression("obj.author == user")
        assert isinstance(result, Compare)
        assert isinstance(result.right, UserRef)


class TestParserLiterals:
    def test_string_literal(self):
        result = parse_expression('"draft"')
        assert result == Literal("draft")

    def test_integer_literal(self):
        result = parse_expression("42")
        assert result == Literal(42)

    def test_float_literal(self):
        result = parse_expression("3.14")
        assert result == Literal(3.14)

    def test_true_literal(self):
        result = parse_expression("true")
        assert result == Literal(True)

    def test_false_literal(self):
        result = parse_expression("false")
        assert result == Literal(False)

    def test_null_literal(self):
        result = parse_expression("null")
        assert result == Literal(None)


class TestParserComparison:
    def test_eq_comparison(self):
        result = parse_expression('obj.status == "draft"')
        assert result == Compare(ObjAttr(["status"]), "==", Literal("draft"))

    def test_ne_comparison(self):
        result = parse_expression('obj.status != "published"')
        assert result == Compare(ObjAttr(["status"]), "!=", Literal("published"))

    def test_gt_comparison(self):
        result = parse_expression("obj.count > 10")
        assert result == Compare(ObjAttr(["count"]), ">", Literal(10))

    def test_lt_comparison(self):
        result = parse_expression("obj.count < 10")
        assert result == Compare(ObjAttr(["count"]), "<", Literal(10))

    def test_ge_comparison(self):
        result = parse_expression("obj.count >= 10")
        assert result == Compare(ObjAttr(["count"]), ">=", Literal(10))

    def test_le_comparison(self):
        result = parse_expression("obj.count <= 10")
        assert result == Compare(ObjAttr(["count"]), "<=", Literal(10))

    def test_obj_author_eq_user(self):
        result = parse_expression("obj.author == user")
        assert isinstance(result, Compare)
        assert result.left == ObjAttr(["author"])
        assert result.op == "=="
        assert isinstance(result.right, UserRef)


class TestParserBooleanOps:
    def test_and_expression(self):
        result = parse_expression("is_admin and is_active")
        assert result == AndExpr(RuleRef("is_admin"), RuleRef("is_active"))

    def test_or_expression(self):
        result = parse_expression("is_admin or is_author")
        assert result == OrExpr(RuleRef("is_admin"), RuleRef("is_author"))

    def test_not_expression(self):
        result = parse_expression("not is_banned")
        assert result == NotExpr(RuleRef("is_banned"))

    def test_complex_and_or(self):
        result = parse_expression("a or b and c")
        assert isinstance(result, OrExpr)
        assert result.left == RuleRef("a")
        assert isinstance(result.right, AndExpr)


class TestParserIn:
    def test_in_list(self):
        result = parse_expression('obj.status in ["draft", "review"]')
        assert isinstance(result, InExpr)
        assert result.left == ObjAttr(["status"])
        assert isinstance(result.right, ListExpr)
        assert len(result.right.items) == 2
        assert result.right.items[0] == Literal("draft")
        assert result.right.items[1] == Literal("review")

    def test_in_empty_list(self):
        result = parse_expression("obj.status in []")
        assert isinstance(result, InExpr)
        assert result.right == ListExpr([])

    def test_in_number_list(self):
        result = parse_expression("obj.priority in [1, 2, 3]")
        assert isinstance(result, InExpr)
        assert len(result.right.items) == 3


class TestParserParentheses:
    def test_simple_parentheses(self):
        result = parse_expression("(is_admin)")
        assert result == RuleRef("is_admin")

    def test_grouping_changes_precedence(self):
        result = parse_expression("(a or b) and c")
        assert isinstance(result, AndExpr)
        assert isinstance(result.left, OrExpr)
        assert result.right == RuleRef("c")

    def test_nested_parentheses(self):
        result = parse_expression("((a and b))")
        assert isinstance(result, AndExpr)


class TestParserComplex:
    def test_complex_expression_1(self):
        result = parse_expression(
            'is_admin or (obj.author == user and obj.status == "draft")'
        )
        assert isinstance(result, OrExpr)
        assert result.left == RuleRef("is_admin")
        assert isinstance(result.right, AndExpr)

    def test_complex_expression_2(self):
        result = parse_expression("user.is_staff and not obj.is_locked")
        assert isinstance(result, AndExpr)
        assert result.left == UserAttr(["is_staff"])
        assert isinstance(result.right, NotExpr)

    def test_complex_expression_3(self):
        result = parse_expression('obj.status in ["draft", "review"] or is_admin')
        assert isinstance(result, OrExpr)
        assert isinstance(result.left, InExpr)
        assert result.right == RuleRef("is_admin")


class TestParserErrors:
    def test_unexpected_token(self):
        with pytest.raises(ExpressionSyntaxError):
            parse_expression("obj.status == == 'draft'")

    def test_unclosed_parenthesis(self):
        with pytest.raises(ExpressionSyntaxError):
            parse_expression("(is_admin and is_author")

    def test_unclosed_bracket(self):
        with pytest.raises(ExpressionSyntaxError):
            parse_expression('obj.status in ["draft", "review"')
