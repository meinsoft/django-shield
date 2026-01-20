import pytest

from django_shield.exceptions import DjangoShieldError, PermissionDenied


class TestDjangoShieldError:
    def test_is_exception(self) -> None:
        assert issubclass(DjangoShieldError, Exception)

    def test_can_be_raised(self) -> None:
        with pytest.raises(DjangoShieldError):
            raise DjangoShieldError("test error")


class TestPermissionDenied:
    def test_inherits_from_django_shield_error(self) -> None:
        assert issubclass(PermissionDenied, DjangoShieldError)

    def test_stores_rule_name(self) -> None:
        exc = PermissionDenied(rule_name="can_edit", user="testuser")
        assert exc.rule_name == "can_edit"

    def test_stores_user(self) -> None:
        exc = PermissionDenied(rule_name="can_edit", user="testuser")
        assert exc.user == "testuser"

    def test_stores_obj_when_provided(self) -> None:
        obj = {"id": 1}
        exc = PermissionDenied(rule_name="can_edit", user="testuser", obj=obj)
        assert exc.obj == obj

    def test_obj_defaults_to_none(self) -> None:
        exc = PermissionDenied(rule_name="can_edit", user="testuser")
        assert exc.obj is None

    def test_message_without_obj(self) -> None:
        exc = PermissionDenied(rule_name="can_edit", user="testuser")
        assert str(exc) == "User 'testuser' does not have permission 'can_edit'"

    def test_message_with_obj(self) -> None:
        exc = PermissionDenied(rule_name="can_edit", user="testuser", obj="Article:1")
        expected = (
            "User 'testuser' does not have permission 'can_edit' for object 'Article:1'"
        )
        assert str(exc) == expected

    def test_can_be_caught_as_django_shield_error(self) -> None:
        with pytest.raises(DjangoShieldError):
            raise PermissionDenied(rule_name="test", user="user")
