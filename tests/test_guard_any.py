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
    def __init__(self, id=1, is_staff=False, is_superuser=False):
        self.id = id
        self.is_staff = is_staff
        self.is_superuser = is_superuser
        self.username = "testuser"


class TestGuardAny:
    def test_one_rule_passes(self, mock_request):
        @rule
        def is_admin(user, obj=None):
            return False

        @rule
        def is_author(user, obj=None):
            return True

        @guard.any("is_admin", "is_author")
        def my_view(request):
            return HttpResponse("OK")

        response = my_view(mock_request)
        assert response.status_code == 200

    def test_first_rule_passes(self, mock_request):
        @rule
        def is_admin(user, obj=None):
            return True

        @rule
        def is_author(user, obj=None):
            return False

        @guard.any("is_admin", "is_author")
        def my_view(request):
            return HttpResponse("OK")

        response = my_view(mock_request)
        assert response.status_code == 200

    def test_all_rules_fail(self, mock_request):
        @rule
        def is_admin(user, obj=None):
            return False

        @rule
        def is_author(user, obj=None):
            return False

        @guard.any("is_admin", "is_author")
        def my_view(request):
            return HttpResponse("OK")

        with pytest.raises(PermissionDenied) as exc_info:
            my_view(mock_request)

        assert exc_info.value.rule_name == "is_author"

    def test_with_expression_rules(self, mock_request):
        mock_request.user.is_staff = False
        mock_request.user.is_superuser = True

        @guard.any("user.is_staff", "user.is_superuser")
        def my_view(request):
            return HttpResponse("OK")

        response = my_view(mock_request)
        assert response.status_code == 200

    def test_with_model_and_lookup(self, mock_request, db):
        article = Article.objects.create(
            title="Test Article",
            slug="test-article",
            author_id=999,
        )
        mock_request.user.is_staff = True

        @guard.any(
            "obj.author_id == user.id",
            "user.is_staff",
            model=Article,
            lookup="pk",
        )
        def my_view(request, pk):
            return HttpResponse("OK")

        response = my_view(mock_request, pk=article.pk)
        assert response.status_code == 200

    def test_with_inject(self, mock_request, db):
        article = Article.objects.create(
            title="Public Article",
            slug="public-article",
            author_id=999,
        )
        mock_request.user.is_staff = True

        @guard.any(
            "obj.author_id == user.id",
            "user.is_staff",
            model=Article,
            lookup="pk",
            inject="article",
        )
        def my_view(request, pk, article=None):
            return HttpResponse(article.title)

        response = my_view(mock_request, pk=article.pk)
        assert response.content == b"Public Article"


class TestGuardAnyCBV:
    def test_cbv_one_rule_passes(self):
        @rule
        def is_admin(user, obj=None):
            return False

        @rule
        def is_author(user, obj=None):
            return True

        @guard.any("is_admin", "is_author")
        class MyView(View):
            def get(self, request):
                return HttpResponse("OK")

        view = MyView()
        request = make_request(MockUser())
        response = view.dispatch(request)
        assert response.status_code == 200

    def test_cbv_all_rules_fail(self):
        @rule
        def is_admin(user, obj=None):
            return False

        @rule
        def is_author(user, obj=None):
            return False

        @guard.any("is_admin", "is_author")
        class MyView(View):
            def get(self, request):
                return HttpResponse("OK")

        view = MyView()
        request = make_request(MockUser())

        with pytest.raises(PermissionDenied) as exc_info:
            view.dispatch(request)

        assert exc_info.value.rule_name == "is_author"

    def test_cbv_with_get_object(self, db):
        article = Article.objects.create(
            title="Test Article",
            slug="test-article",
            author_id=999,
        )

        @guard.any("obj.author_id == user.id", "user.is_staff")
        class MyView(View):
            def get_object(self):
                return article

            def get(self, request):
                return HttpResponse("OK")

        view = MyView()
        request = make_request(MockUser(id=1, is_staff=True))
        response = view.dispatch(request)
        assert response.status_code == 200
