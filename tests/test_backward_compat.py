from unittest.mock import MagicMock

import pytest
from django.http import HttpResponse

from django_shield.exceptions import PermissionDenied
from django_shield.guard import guard
from django_shield.rules import Rule, RuleRegistry, rule


class MockUser:
    def __init__(self, id=1, is_staff=False, is_superuser=False):
        self.id = id
        self.is_staff = is_staff
        self.is_superuser = is_superuser


class MockPost:
    def __init__(self, pk=1, author_id=1, status="draft"):
        self.pk = pk
        self.author_id = author_id
        self.status = status

    class DoesNotExist(Exception):
        pass

    class objects:
        @staticmethod
        def get(**kwargs):
            return MockPost()


@pytest.fixture(autouse=True)
def clear_registry():
    RuleRegistry.clear()
    yield
    RuleRegistry.clear()


class TestV010RuleStillWorks:
    def test_rule_decorator_without_args(self):
        @rule
        def is_admin(user):
            return user.is_superuser

        assert RuleRegistry.exists("is_admin")

    def test_rule_decorator_with_name(self):
        @rule(name="custom_rule")
        def my_rule(user):
            return True

        assert RuleRegistry.exists("custom_rule")
        assert not RuleRegistry.exists("my_rule")

    def test_rule_check_method(self):
        @rule
        def is_staff(user):
            return user.is_staff

        r = RuleRegistry.get("is_staff")
        assert r.check(MockUser(is_staff=True)) is True
        assert r.check(MockUser(is_staff=False)) is False

    def test_rule_with_object(self):
        @rule
        def is_author(user, post):
            return post.author_id == user.id

        r = RuleRegistry.get("is_author")
        user = MockUser(id=1)
        post = MockPost(author_id=1)
        assert r.check(user, post) is True


class TestV010GuardStillWorks:
    def test_guard_fbv_basic(self):
        @rule
        def always_allow(user):
            return True

        @guard("always_allow")
        def my_view(request):
            return HttpResponse("success")

        request = MagicMock()
        request.user = MockUser()

        response = my_view(request)
        assert response.content == b"success"

    def test_guard_fbv_denies(self):
        @rule
        def always_deny(user):
            return False

        @guard("always_deny")
        def my_view(request):
            return HttpResponse("success")

        request = MagicMock()
        request.user = MockUser()

        with pytest.raises(PermissionDenied):
            my_view(request)

    def test_guard_fbv_with_model(self):
        @rule
        def can_edit(user, post):
            return post.author_id == user.id

        @guard("can_edit", model=MockPost)
        def edit_view(request, pk):
            return HttpResponse("edit")

        request = MagicMock()
        request.user = MockUser(id=1)

        response = edit_view(request, pk=1)
        assert response.content == b"edit"

    def test_guard_fbv_with_inject(self):
        @rule
        def can_view(user, post):
            return True

        @guard("can_view", model=MockPost, inject="post")
        def view(request, pk, post=None):
            return HttpResponse(f"post: {post.pk}")

        request = MagicMock()
        request.user = MockUser()

        response = view(request, pk=1)
        assert b"post: 1" in response.content


class TestMixingOldRulesWithExpressions:
    def test_old_rule_in_expression(self):
        @rule
        def is_admin(user):
            return user.is_superuser

        @guard("is_admin or user.is_staff")
        def admin_view(request):
            return HttpResponse("admin")

        request = MagicMock()
        request.user = MockUser(is_superuser=False, is_staff=True)

        response = admin_view(request)
        assert response.content == b"admin"

    def test_old_rule_takes_precedence(self):
        @rule
        def is_admin(user):
            return user.is_superuser

        @guard("is_admin")
        def admin_view(request):
            return HttpResponse("admin")

        request = MagicMock()
        request.user = MockUser(is_superuser=True)

        response = admin_view(request)
        assert response.content == b"admin"

    def test_expression_when_rule_not_found(self):
        @guard("user.is_staff")
        def staff_view(request):
            return HttpResponse("staff")

        request = MagicMock()
        request.user = MockUser(is_staff=True)

        response = staff_view(request)
        assert response.content == b"staff"


class TestRuleRegistryV010:
    def test_register_method(self):
        r = Rule("test_rule", lambda u: True)
        RuleRegistry.register(r)
        assert RuleRegistry.exists("test_rule")

    def test_get_method(self):
        r = Rule("test_rule", lambda u: True)
        RuleRegistry.register(r)
        assert RuleRegistry.get("test_rule") is r

    def test_exists_method(self):
        assert not RuleRegistry.exists("nonexistent")
        r = Rule("test_rule", lambda u: True)
        RuleRegistry.register(r)
        assert RuleRegistry.exists("test_rule")

    def test_clear_method(self):
        r = Rule("test_rule", lambda u: True)
        RuleRegistry.register(r)
        RuleRegistry.clear()
        assert not RuleRegistry.exists("test_rule")
