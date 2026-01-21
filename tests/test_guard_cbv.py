from unittest.mock import MagicMock

import pytest
from django.http import HttpResponse
from django.views import View

from django_shield.exceptions import PermissionDenied
from django_shield.guard import guard
from django_shield.rules import RuleRegistry, rule


class MockUser:
    def __init__(self, id=1, is_staff=False):
        self.id = id
        self.is_staff = is_staff


class MockPost:
    def __init__(self, author_id=1, title="Test Post"):
        self.pk = 1
        self.author_id = author_id
        self.title = title


def make_request(user, method="GET"):
    request = MagicMock()
    request.user = user
    request.method = method
    return request


@pytest.fixture(autouse=True)
def clear_registry():
    RuleRegistry.clear()
    yield
    RuleRegistry.clear()


class TestGuardCBVBasic:
    def test_cbv_allows_authorized_user(self):
        @rule
        def always_allow(user, obj=None):
            return True

        @guard("always_allow")
        class TestView(View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("success")

        view = TestView()
        request = make_request(MockUser())

        response = view.dispatch(request)
        assert response.content == b"success"

    def test_cbv_denies_unauthorized_user(self):
        @rule
        def always_deny(user, obj=None):
            return False

        @guard("always_deny")
        class TestView(View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("success")

        view = TestView()
        request = make_request(MockUser())

        with pytest.raises(PermissionDenied):
            view.dispatch(request)


class TestGuardCBVWithObject:
    def test_cbv_with_get_object(self):
        @rule
        def is_author(user, obj):
            return obj.author_id == user.id

        @guard("is_author")
        class TestView(View):
            def get_object(self):
                return MockPost(author_id=1)

            def get(self, request, *args, **kwargs):
                return HttpResponse("success")

        view = TestView()
        request = make_request(MockUser(id=1))

        response = view.dispatch(request)
        assert response.content == b"success"

    def test_cbv_denies_when_not_author(self):
        @rule
        def is_author(user, obj):
            return obj.author_id == user.id

        @guard("is_author")
        class TestView(View):
            def get_object(self):
                return MockPost(author_id=999)

            def get(self, request, *args, **kwargs):
                return HttpResponse("success")

        view = TestView()
        request = make_request(MockUser(id=1))

        with pytest.raises(PermissionDenied):
            view.dispatch(request)


class TestGuardCBVUpdateView:
    def test_update_view_with_staff_rule(self):
        @rule
        def is_staff(user, obj=None):
            return user.is_staff

        @guard("is_staff")
        class TestView(View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("updated")

        view = TestView()
        request = make_request(MockUser(is_staff=True))

        response = view.dispatch(request)
        assert response.content == b"updated"

    def test_update_view_denies_non_staff(self):
        @rule
        def is_staff(user, obj=None):
            return user.is_staff

        @guard("is_staff")
        class TestView(View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("updated")

        view = TestView()
        request = make_request(MockUser(is_staff=False))

        with pytest.raises(PermissionDenied):
            view.dispatch(request)


class TestGuardCBVDeleteView:
    def test_delete_view_allows_owner(self):
        @rule
        def is_owner(user, obj):
            return obj.author_id == user.id

        @guard("is_owner")
        class TestView(View):
            def get_object(self):
                return MockPost(author_id=1)

            def delete(self, request, *args, **kwargs):
                return HttpResponse("deleted")

        view = TestView()
        request = make_request(MockUser(id=1), method="DELETE")

        response = view.dispatch(request)
        assert response.content == b"deleted"


class TestGuardCBVDetailView:
    def test_detail_view_allows_access(self):
        @rule
        def can_view(user, obj):
            return True

        @guard("can_view")
        class TestView(View):
            def get_object(self):
                return MockPost()

            def get(self, request, *args, **kwargs):
                return HttpResponse("detail")

        view = TestView()
        request = make_request(MockUser())

        response = view.dispatch(request)
        assert response.content == b"detail"


class TestGuardCBVListView:
    def test_list_view_without_object(self):
        @rule
        def is_authenticated(user, obj=None):
            return user.id is not None

        @guard("is_authenticated")
        class TestView(View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("list")

        view = TestView()
        request = make_request(MockUser())

        response = view.dispatch(request)
        assert response.content == b"list"

    def test_list_view_denies_unauthenticated(self):
        @rule
        def is_authenticated(user, obj=None):
            return user.id is not None

        @guard("is_authenticated")
        class TestView(View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("list")

        view = TestView()
        request = make_request(MockUser(id=None))

        with pytest.raises(PermissionDenied):
            view.dispatch(request)


class TestGuardCBVGetObjectFails:
    def test_cbv_continues_when_get_object_raises(self):
        @rule
        def always_allow(user, obj=None):
            return True

        @guard("always_allow")
        class TestView(View):
            def get_object(self):
                raise Exception("Object not found")

            def get(self, request, *args, **kwargs):
                return HttpResponse("success")

        view = TestView()
        request = make_request(MockUser())

        response = view.dispatch(request)
        assert response.content == b"success"
