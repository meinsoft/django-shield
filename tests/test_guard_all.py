from unittest.mock import MagicMock

import pytest
from django.http import HttpResponse
from django.views import View

from django_shield import guard
from django_shield.exceptions import PermissionDenied
from django_shield.rules import rule

from .models import Article


def make_request(user, method="GET"):
    request = MagicMock()
    request.user = user
    request.method = method
    return request


class MockUser:
    def __init__(self, id=1, is_staff=False):
        self.id = id
        self.is_staff = is_staff
        self.username = "testuser"


class TestGuardAll:
    def test_all_rules_pass(self, mock_request):
        @rule
        def is_authenticated(user, obj=None):
            return True

        @rule
        def is_active(user, obj=None):
            return True

        @guard.all("is_authenticated", "is_active")
        def my_view(request):
            return HttpResponse("OK")

        response = my_view(mock_request)
        assert response.status_code == 200

    def test_one_rule_fails(self, mock_request):
        @rule
        def is_authenticated(user, obj=None):
            return True

        @rule
        def is_admin(user, obj=None):
            return False

        @guard.all("is_authenticated", "is_admin")
        def my_view(request):
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied) as exc_info:
            my_view(mock_request)

        assert exc_info.value.rule_name == "is_admin"

    def test_first_rule_fails(self, mock_request):
        @rule
        def first_rule(user, obj=None):
            return False

        @rule
        def second_rule(user, obj=None):
            return True

        @guard.all("first_rule", "second_rule")
        def my_view(request):
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied) as exc_info:
            my_view(mock_request)

        assert exc_info.value.rule_name == "first_rule"

    def test_with_expression_rules(self, mock_request):
        mock_request.user.is_staff = True

        @guard.all("user.is_staff", "True")
        def my_view(request):
            return HttpResponse("OK")

        response = my_view(mock_request)
        assert response.status_code == 200

    def test_with_model_and_lookup(self, mock_request, db):
        article = Article.objects.create(
            title="Test Article",
            slug="test-article",
            author_id=mock_request.user.id,
        )

        @guard.all(
            "obj.author_id == user.id",
            "obj.slug == \"test-article\"",
            model=Article,
            lookup="pk",
        )
        def my_view(request, pk):
            return HttpResponse("OK")

        response = my_view(mock_request, pk=article.pk)
        assert response.status_code == 200

    def test_with_inject(self, mock_request, db):
        article = Article.objects.create(
            title="Test Article",
            slug="test-article",
            author_id=mock_request.user.id,
        )

        @guard.all(
            "obj.author_id == user.id",
            model=Article,
            lookup="pk",
            inject="article",
        )
        def my_view(request, pk, article=None):
            return HttpResponse(article.title)

        response = my_view(mock_request, pk=article.pk)
        assert response.content == b"Test Article"


class TestGuardAllCBV:
    def test_cbv_all_rules_pass(self):
        @rule
        def is_authenticated(user, obj=None):
            return True

        @rule
        def is_active(user, obj=None):
            return True

        @guard.all("is_authenticated", "is_active")
        class MyView(View):
            def get(self, request):
                return HttpResponse("OK")

        view = MyView()
        request = make_request(MockUser())
        response = view.dispatch(request)
        assert response.status_code == 200

    def test_cbv_one_rule_fails(self):
        @rule
        def is_authenticated(user, obj=None):
            return True

        @rule
        def is_admin(user, obj=None):
            return False

        @guard.all("is_authenticated", "is_admin")
        class MyView(View):
            def get(self, request):
                return HttpResponse("OK")

        view = MyView()
        request = make_request(MockUser())

        with pytest.raises(PermissionDenied) as exc_info:
            view.dispatch(request)

        assert exc_info.value.rule_name == "is_admin"

    def test_cbv_with_get_object(self, db):
        article = Article.objects.create(
            title="Test Article",
            slug="test-article",
            author_id=1,
        )

        @guard.all("obj.author_id == user.id", "obj.slug == \"test-article\"")
        class MyView(View):
            def get_object(self):
                return article

            def get(self, request):
                return HttpResponse("OK")

        view = MyView()
        request = make_request(MockUser(id=1))
        response = view.dispatch(request)
        assert response.status_code == 200
