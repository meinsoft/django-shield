from unittest.mock import MagicMock

import django
import pytest
from django.conf import settings
from django.http import HttpRequest

from django_shield.expressions.cache import clear_cache
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
    def __init__(self, id=1, username="testuser", is_staff=False, is_superuser=False):
        self.id = id
        self.username = username
        self.is_staff = is_staff
        self.is_superuser = is_superuser

    def __str__(self):
        return self.username


@pytest.fixture
def mock_user():
    return MockUser()


@pytest.fixture
def staff_user():
    return MockUser(id=2, username="staffuser", is_staff=True)


@pytest.fixture
def superuser():
    return MockUser(id=3, username="superuser", is_superuser=True)


@pytest.fixture
def mock_request(mock_user):
    request = MagicMock(spec=HttpRequest)
    request.user = mock_user
    return request


@pytest.fixture
def staff_request(staff_user):
    request = MagicMock(spec=HttpRequest)
    request.user = staff_user
    return request


@pytest.fixture(autouse=True)
def clear_rule_registry():
    RuleRegistry.clear()
    clear_cache()
    yield
    RuleRegistry.clear()
    clear_cache()
