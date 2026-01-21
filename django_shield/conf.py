from django.conf import settings


def get_shield_settings():
    return getattr(settings, "DJANGO_SHIELD", {})


def is_debug_enabled():
    shield_settings = get_shield_settings()
    return shield_settings.get("DEBUG", False)
