from django.conf import settings
from django.http import HttpResponse

from django_shield import guard
from django_shield.rules import rule

from .models import Article


class TestDebugMode:
    def test_debug_output_when_enabled(self, mock_request, capsys):
        settings.DJANGO_SHIELD = {"DEBUG": True}

        @rule
        def is_active(user, obj=None):
            return True

        @guard("is_active")
        def my_view(request):
            return HttpResponse("OK")

        my_view(mock_request)

        captured = capsys.readouterr()
        assert "[Django Shield] Checking: is_active" in captured.out
        assert "[Django Shield] User: testuser (id=1)" in captured.out
        assert "[Django Shield] Object: None" in captured.out
        assert "[Django Shield] Result: ALLOWED" in captured.out

        del settings.DJANGO_SHIELD

    def test_no_output_when_disabled(self, mock_request, capsys):
        settings.DJANGO_SHIELD = {"DEBUG": False}

        @rule
        def is_active(user, obj=None):
            return True

        @guard("is_active")
        def my_view(request):
            return HttpResponse("OK")

        my_view(mock_request)

        captured = capsys.readouterr()
        assert "[Django Shield]" not in captured.out

        del settings.DJANGO_SHIELD

    def test_no_output_when_no_settings(self, mock_request, capsys):
        if hasattr(settings, "DJANGO_SHIELD"):
            del settings.DJANGO_SHIELD

        @rule
        def is_active(user, obj=None):
            return True

        @guard("is_active")
        def my_view(request):
            return HttpResponse("OK")

        my_view(mock_request)

        captured = capsys.readouterr()
        assert "[Django Shield]" not in captured.out

    def test_debug_with_object(self, mock_request, db, capsys):
        settings.DJANGO_SHIELD = {"DEBUG": True}

        article = Article.objects.create(
            title="Test Article",
            slug="test-article",
            author_id=mock_request.user.id,
        )

        @guard("obj.author_id == user.id", model=Article, lookup="pk")
        def my_view(request, pk):
            return HttpResponse("OK")

        my_view(mock_request, pk=article.pk)

        captured = capsys.readouterr()
        assert "[Django Shield] Object: Article" in captured.out
        assert f"(id={article.pk})" in captured.out

        del settings.DJANGO_SHIELD

    def test_debug_denied_result(self, mock_request, capsys):
        settings.DJANGO_SHIELD = {"DEBUG": True}

        @rule
        def is_admin(user, obj=None):
            return False

        @guard("is_admin")
        def my_view(request):
            return HttpResponse("OK")

        try:
            my_view(mock_request)
        except Exception:
            pass

        captured = capsys.readouterr()
        assert "[Django Shield] Result: DENIED" in captured.out

        del settings.DJANGO_SHIELD

    def test_debug_with_guard_all(self, mock_request, capsys):
        settings.DJANGO_SHIELD = {"DEBUG": True}

        @rule
        def first_rule(user, obj=None):
            return True

        @rule
        def second_rule(user, obj=None):
            return True

        @guard.all("first_rule", "second_rule")
        def my_view(request):
            return HttpResponse("OK")

        my_view(mock_request)

        captured = capsys.readouterr()
        assert "[Django Shield] Checking: first_rule" in captured.out
        assert "[Django Shield] Checking: second_rule" in captured.out

        del settings.DJANGO_SHIELD

    def test_debug_with_guard_any(self, mock_request, capsys):
        settings.DJANGO_SHIELD = {"DEBUG": True}

        @rule
        def first_rule(user, obj=None):
            return False

        @rule
        def second_rule(user, obj=None):
            return True

        @guard.any("first_rule", "second_rule")
        def my_view(request):
            return HttpResponse("OK")

        my_view(mock_request)

        captured = capsys.readouterr()
        assert "[Django Shield] Checking: first_rule" in captured.out
        assert "[Django Shield] Checking: second_rule" in captured.out

        del settings.DJANGO_SHIELD
