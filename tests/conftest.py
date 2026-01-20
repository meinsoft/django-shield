from typing import Any
from unittest.mock import MagicMock

import django
import pytest
from django.conf import settings
from django.http import HttpRequest

from django_shield.rules import RuleRegistry

if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "tests",
        ],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    )
    django.setup()


class MockUser:
    def __init__(
        self,
        id: int = 1,
        username: str = "testuser",
        is_staff: bool = False,
        is_superuser: bool = False,
    ) -> None:
        self.id = id
        self.username = username
        self.is_staff = is_staff
        self.is_superuser = is_superuser

    def __str__(self) -> str:
        return self.username


@pytest.fixture
def mock_user() -> MockUser:
    return MockUser()


@pytest.fixture
def staff_user() -> MockUser:
    return MockUser(id=2, username="staffuser", is_staff=True)


@pytest.fixture
def superuser() -> MockUser:
    return MockUser(id=3, username="superuser", is_superuser=True)


@pytest.fixture
def mock_request(mock_user: MockUser) -> HttpRequest:
    request = MagicMock(spec=HttpRequest)
    request.user = mock_user
    return request


@pytest.fixture
def staff_request(staff_user: MockUser) -> HttpRequest:
    request = MagicMock(spec=HttpRequest)
    request.user = staff_user
    return request


@pytest.fixture(autouse=True)
def clear_rule_registry() -> Any:
    RuleRegistry.clear()
    yield
    RuleRegistry.clear()
