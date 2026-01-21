import pytest

from django_shield.exceptions import ExpressionEvaluationError
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
from django_shield.expressions.evaluator import evaluate
from django_shield.rules import RuleRegistry, rule


class MockUser:
    def __init__(self, id=1, is_staff=False, is_superuser=False):
        self.id = id
        self.is_staff = is_staff
        self.is_superuser = is_superuser
        self.profile = MockProfile()


class MockProfile:
    def __init__(self):
        self.name = "Test User"


class MockPost:
    def __init__(self, author=None, status="draft", count=5):
        self.author = author
        self.status = status
        self.count = count
        self.is_locked = False


@pytest.fixture(autouse=True)
def clear_registry():
    RuleRegistry.clear()
    yield
    RuleRegistry.clear()


class TestEvaluateRuleRef:
    def test_rule_returns_true(self):
        @rule
        def always_true(user):
            return True

        node = RuleRef("always_true")
        assert evaluate(node, MockUser()) is True

    def test_rule_returns_false(self):
        @rule
        def always_false(user):
            return False

        node = RuleRef("always_false")
        assert evaluate(node, MockUser()) is False

    def test_rule_with_object(self):
        @rule
        def is_owner(user, obj):
            return obj.author == user

        user = MockUser()
        post = MockPost(author=user)
        node = RuleRef("is_owner")
        assert evaluate(node, user, post) is True

    def test_unknown_rule_raises_error(self):
        node = RuleRef("nonexistent")
        with pytest.raises(ExpressionEvaluationError) as exc_info:
            evaluate(node, MockUser())
        assert "Rule 'nonexistent' is not registered" in str(exc_info.value)


class TestEvaluateObjAttr:
    def test_single_attribute(self):
        post = MockPost(status="draft")
        node = ObjAttr(["status"])
        assert evaluate(node, MockUser(), post) == "draft"

    def test_nested_attribute(self):
        user = MockUser()
        post = MockPost(author=user)
        node = ObjAttr(["author", "id"])
        assert evaluate(node, MockUser(), post) == 1

    def test_obj_is_none_raises_error(self):
        node = ObjAttr(["status"])
        with pytest.raises(ExpressionEvaluationError) as exc_info:
            evaluate(node, MockUser(), None)
        assert "Object is None" in str(exc_info.value)

    def test_missing_attribute_returns_none(self):
        post = MockPost()
        node = ObjAttr(["nonexistent"])
        assert evaluate(node, MockUser(), post) is None


class TestEvaluateUserAttr:
    def test_single_attribute(self):
        user = MockUser(is_staff=True)
        node = UserAttr(["is_staff"])
        assert evaluate(node, user) is True

    def test_nested_attribute(self):
        user = MockUser()
        node = UserAttr(["profile", "name"])
        assert evaluate(node, user) == "Test User"


class TestEvaluateUserRef:
    def test_returns_user(self):
        user = MockUser()
        node = UserRef()
        assert evaluate(node, user) is user


class TestEvaluateLiteral:
    def test_string(self):
        node = Literal("hello")
        assert evaluate(node, MockUser()) == "hello"

    def test_number(self):
        node = Literal(42)
        assert evaluate(node, MockUser()) == 42

    def test_boolean(self):
        node = Literal(True)
        assert evaluate(node, MockUser()) is True

    def test_none(self):
        node = Literal(None)
        assert evaluate(node, MockUser()) is None


class TestEvaluateCompare:
    def test_eq_true(self):
        post = MockPost(status="draft")
        node = Compare(ObjAttr(["status"]), "==", Literal("draft"))
        assert evaluate(node, MockUser(), post) is True

    def test_eq_false(self):
        post = MockPost(status="published")
        node = Compare(ObjAttr(["status"]), "==", Literal("draft"))
        assert evaluate(node, MockUser(), post) is False

    def test_ne_true(self):
        post = MockPost(status="published")
        node = Compare(ObjAttr(["status"]), "!=", Literal("draft"))
        assert evaluate(node, MockUser(), post) is True

    def test_gt(self):
        post = MockPost(count=10)
        node = Compare(ObjAttr(["count"]), ">", Literal(5))
        assert evaluate(node, MockUser(), post) is True

    def test_lt(self):
        post = MockPost(count=3)
        node = Compare(ObjAttr(["count"]), "<", Literal(5))
        assert evaluate(node, MockUser(), post) is True

    def test_ge(self):
        post = MockPost(count=5)
        node = Compare(ObjAttr(["count"]), ">=", Literal(5))
        assert evaluate(node, MockUser(), post) is True

    def test_le(self):
        post = MockPost(count=5)
        node = Compare(ObjAttr(["count"]), "<=", Literal(5))
        assert evaluate(node, MockUser(), post) is True

    def test_obj_author_eq_user(self):
        user = MockUser()
        post = MockPost(author=user)
        node = Compare(ObjAttr(["author"]), "==", UserRef())
        assert evaluate(node, user, post) is True

    def test_obj_author_ne_user(self):
        user = MockUser(id=1)
        other_user = MockUser(id=2)
        post = MockPost(author=other_user)
        node = Compare(ObjAttr(["author"]), "==", UserRef())
        assert evaluate(node, user, post) is False

    def test_null_comparison(self):
        post = MockPost()
        post.deleted_at = None
        node = Compare(ObjAttr(["deleted_at"]), "==", Literal(None))
        assert evaluate(node, MockUser(), post) is True


class TestEvaluateAnd:
    def test_both_true(self):
        node = AndExpr(Literal(True), Literal(True))
        assert evaluate(node, MockUser()) is True

    def test_left_false(self):
        node = AndExpr(Literal(False), Literal(True))
        assert evaluate(node, MockUser()) is False

    def test_right_false(self):
        node = AndExpr(Literal(True), Literal(False))
        assert evaluate(node, MockUser()) is False

    def test_short_circuit(self):
        @rule
        def should_not_be_called(user):
            raise Exception("Should not be called")

        node = AndExpr(Literal(False), RuleRef("should_not_be_called"))
        assert evaluate(node, MockUser()) is False


class TestEvaluateOr:
    def test_both_true(self):
        node = OrExpr(Literal(True), Literal(True))
        assert evaluate(node, MockUser()) is True

    def test_left_true(self):
        node = OrExpr(Literal(True), Literal(False))
        assert evaluate(node, MockUser()) is True

    def test_both_false(self):
        node = OrExpr(Literal(False), Literal(False))
        assert evaluate(node, MockUser()) is False

    def test_short_circuit(self):
        @rule
        def should_not_be_called(user):
            raise Exception("Should not be called")

        node = OrExpr(Literal(True), RuleRef("should_not_be_called"))
        assert evaluate(node, MockUser()) is True


class TestEvaluateNot:
    def test_not_true(self):
        node = NotExpr(Literal(True))
        assert evaluate(node, MockUser()) is False

    def test_not_false(self):
        node = NotExpr(Literal(False))
        assert evaluate(node, MockUser()) is True


class TestEvaluateIn:
    def test_in_list_true(self):
        post = MockPost(status="draft")
        node = InExpr(
            ObjAttr(["status"]), ListExpr([Literal("draft"), Literal("review")])
        )
        assert evaluate(node, MockUser(), post) is True

    def test_in_list_false(self):
        post = MockPost(status="published")
        node = InExpr(
            ObjAttr(["status"]), ListExpr([Literal("draft"), Literal("review")])
        )
        assert evaluate(node, MockUser(), post) is False

    def test_in_empty_list(self):
        post = MockPost(status="draft")
        node = InExpr(ObjAttr(["status"]), ListExpr([]))
        assert evaluate(node, MockUser(), post) is False


class TestEvaluateComplex:
    def test_is_admin_or_is_author(self):
        @rule
        def is_admin(user, obj=None):
            return user.is_superuser

        user = MockUser(is_superuser=False)
        post = MockPost(author=user)

        node = OrExpr(
            RuleRef("is_admin"),
            Compare(ObjAttr(["author"]), "==", UserRef()),
        )
        assert evaluate(node, user, post) is True

    def test_staff_and_not_locked(self):
        user = MockUser(is_staff=True)
        post = MockPost()
        post.is_locked = False

        node = AndExpr(
            UserAttr(["is_staff"]),
            NotExpr(ObjAttr(["is_locked"])),
        )
        assert evaluate(node, user, post) is True
