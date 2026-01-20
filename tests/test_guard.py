from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import HttpRequest, HttpResponse

from django_shield.exceptions import PermissionDenied
from django_shield.guard import guard
from django_shield.rules import rule

from .conftest import MockUser
from .models import Article


class TestGuardBasic:
    def test_allows_authorized_user(self, mock_request: HttpRequest) -> None:
        @rule
        def always_allow(user: Any) -> bool:
            return True

        @guard("always_allow")
        def my_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("success")

        response = my_view(mock_request)
        assert response.content == b"success"

    def test_denies_unauthorized_user(self, mock_request: HttpRequest) -> None:
        @rule
        def always_deny(user: Any) -> bool:
            return False

        @guard("always_deny")
        def my_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("success")

        with pytest.raises(PermissionDenied) as exc_info:
            my_view(mock_request)

        assert exc_info.value.rule_name == "always_deny"

    def test_raises_value_error_for_unknown_rule(
        self, mock_request: HttpRequest
    ) -> None:
        @guard("nonexistent_rule")
        def my_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("success")

        with pytest.raises(ValueError) as exc_info:
            my_view(mock_request)

        assert "Rule 'nonexistent_rule' not found" in str(exc_info.value)

    def test_preserves_view_function_metadata(self) -> None:
        @rule
        def test_rule(user: Any) -> bool:
            return True

        @guard("test_rule")
        def my_view_function(request: HttpRequest) -> HttpResponse:
            return HttpResponse("success")

        assert my_view_function.__name__ == "my_view_function"


class TestGuardWithModel:
    @pytest.fixture
    def mock_article(self) -> MagicMock:
        article = MagicMock(spec=Article)
        article.id = 1
        article.title = "Test Article"
        article.author_id = 1
        return article

    def test_fetches_object_from_database(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        @rule
        def can_view_article(user: Any, article: Article) -> bool:
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            @guard("can_view_article", model=Article)
            def view_article(request: HttpRequest, pk: int) -> HttpResponse:
                return HttpResponse("success")

            response = view_article(mock_request, pk=1)

            mock_manager.get.assert_called_once_with(pk=1)
            assert response.content == b"success"

    def test_raises_django_permission_denied_when_object_not_found(
        self, mock_request: HttpRequest
    ) -> None:
        @rule
        def can_view_article(user: Any, article: Article) -> bool:
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.side_effect = Article.DoesNotExist()

            @guard("can_view_article", model=Article)
            def view_article(request: HttpRequest, pk: int) -> HttpResponse:
                return HttpResponse("success")

            with pytest.raises(DjangoPermissionDenied):
                view_article(mock_request, pk=999)

    def test_raises_django_permission_denied_when_lookup_value_missing(
        self, mock_request: HttpRequest
    ) -> None:
        @rule
        def can_view_article(user: Any, article: Article) -> bool:
            return True

        @guard("can_view_article", model=Article)
        def view_article(request: HttpRequest) -> HttpResponse:
            return HttpResponse("success")

        with pytest.raises(DjangoPermissionDenied):
            view_article(mock_request)

    def test_passes_object_to_rule_check(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        received_obj: list = []

        @rule
        def can_edit_article(user: Any, article: Article) -> bool:
            received_obj.append(article)
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            @guard("can_edit_article", model=Article)
            def edit_article(request: HttpRequest, pk: int) -> HttpResponse:
                return HttpResponse("success")

            edit_article(mock_request, pk=1)

            assert len(received_obj) == 1
            assert received_obj[0] is mock_article


class TestGuardCustomLookup:
    @pytest.fixture
    def mock_article(self) -> MagicMock:
        article = MagicMock(spec=Article)
        article.id = 1
        article.slug = "test-article"
        return article

    def test_custom_lookup_parameter(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        @rule
        def can_view(user: Any, article: Article) -> bool:
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            @guard("can_view", model=Article, lookup="article_id")
            def view_article(request: HttpRequest, article_id: int) -> HttpResponse:
                return HttpResponse("success")

            view_article(mock_request, article_id=1)

            mock_manager.get.assert_called_once_with(pk=1)

    def test_custom_lookup_field(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        @rule
        def can_view(user: Any, article: Article) -> bool:
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            @guard("can_view", model=Article, lookup="slug", lookup_field="slug")
            def view_article(request: HttpRequest, slug: str) -> HttpResponse:
                return HttpResponse("success")

            view_article(mock_request, slug="test-article")

            mock_manager.get.assert_called_once_with(slug="test-article")

    def test_custom_lookup_and_lookup_field_combined(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        @rule
        def can_view(user: Any, article: Article) -> bool:
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            @guard(
                "can_view",
                model=Article,
                lookup="article_slug",
                lookup_field="slug",
            )
            def view_article(request: HttpRequest, article_slug: str) -> HttpResponse:
                return HttpResponse("success")

            view_article(mock_request, article_slug="my-slug")

            mock_manager.get.assert_called_once_with(slug="my-slug")


class TestGuardInject:
    @pytest.fixture
    def mock_article(self) -> MagicMock:
        article = MagicMock(spec=Article)
        article.id = 1
        article.title = "Test Article"
        return article

    def test_inject_passes_object_to_view(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        @rule
        def can_view(user: Any, article: Article) -> bool:
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            received_article: list = []

            @guard("can_view", model=Article, inject="article")
            def view_article(
                request: HttpRequest, pk: int, article: Article
            ) -> HttpResponse:
                received_article.append(article)
                return HttpResponse("success")

            view_article(mock_request, pk=1)

            assert len(received_article) == 1
            assert received_article[0] is mock_article

    def test_inject_with_custom_parameter_name(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        @rule
        def can_view(user: Any, obj: Article) -> bool:
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            received_obj: list = []

            @guard("can_view", model=Article, inject="obj")
            def view_article(
                request: HttpRequest, pk: int, obj: Article
            ) -> HttpResponse:
                received_obj.append(obj)
                return HttpResponse("success")

            view_article(mock_request, pk=1)

            assert received_obj[0] is mock_article

    def test_inject_not_used_when_not_specified(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        @rule
        def can_view(user: Any, article: Article) -> bool:
            return True

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            kwargs_received: list = []

            @guard("can_view", model=Article)
            def view_article(
                request: HttpRequest, pk: int, **kwargs: Any
            ) -> HttpResponse:
                kwargs_received.append(kwargs)
                return HttpResponse("success")

            view_article(mock_request, pk=1)

            assert "article" not in kwargs_received[0]


class TestGuardPermissionDenied:
    @pytest.fixture
    def mock_article(self) -> MagicMock:
        article = MagicMock(spec=Article)
        article.id = 1
        article.author_id = 999
        return article

    def test_permission_denied_includes_rule_name(
        self, mock_request: HttpRequest
    ) -> None:
        @rule
        def specific_rule(user: Any) -> bool:
            return False

        @guard("specific_rule")
        def my_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("success")

        with pytest.raises(PermissionDenied) as exc_info:
            my_view(mock_request)

        assert exc_info.value.rule_name == "specific_rule"

    def test_permission_denied_includes_user(
        self, mock_request: HttpRequest, mock_user: MockUser
    ) -> None:
        @rule
        def deny_rule(user: Any) -> bool:
            return False

        @guard("deny_rule")
        def my_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("success")

        with pytest.raises(PermissionDenied) as exc_info:
            my_view(mock_request)

        assert exc_info.value.user is mock_user

    def test_permission_denied_includes_object(
        self, mock_request: HttpRequest, mock_article: MagicMock
    ) -> None:
        @rule
        def is_author(user: MockUser, article: Article) -> bool:
            return user.id == article.author_id

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            @guard("is_author", model=Article)
            def edit_article(request: HttpRequest, pk: int) -> HttpResponse:
                return HttpResponse("success")

            with pytest.raises(PermissionDenied) as exc_info:
                edit_article(mock_request, pk=1)

            assert exc_info.value.obj is mock_article


class TestGuardIntegration:
    def test_staff_only_rule(
        self, mock_request: HttpRequest, staff_request: HttpRequest
    ) -> None:
        @rule
        def is_staff(user: MockUser) -> bool:
            return user.is_staff

        @guard("is_staff")
        def admin_view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("admin content")

        with pytest.raises(PermissionDenied):
            admin_view(mock_request)

        response = admin_view(staff_request)
        assert response.content == b"admin content"

    def test_object_owner_rule(
        self, mock_request: HttpRequest, mock_user: MockUser
    ) -> None:
        @rule
        def is_owner(user: MockUser, article: Article) -> bool:
            return user.id == article.author_id

        mock_article = MagicMock(spec=Article)
        mock_article.author_id = mock_user.id

        with patch.object(Article, "objects") as mock_manager:
            mock_manager.get.return_value = mock_article

            @guard("is_owner", model=Article, inject="article")
            def edit_article(
                request: HttpRequest, pk: int, article: Article
            ) -> HttpResponse:
                return HttpResponse(f"editing {article.author_id}")

            response = edit_article(mock_request, pk=1)
            assert response.content == f"editing {mock_user.id}".encode()
