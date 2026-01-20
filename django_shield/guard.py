from functools import wraps

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

from django_shield.exceptions import PermissionDenied
from django_shield.rules import RuleRegistry


def guard(rule_name, *, model=None, lookup="pk", lookup_field="pk", inject=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            obj = None
            if model is not None:
                lookup_value = kwargs.get(lookup)
                if lookup_value is None:
                    raise DjangoPermissionDenied("Object not found")
                try:
                    obj = model.objects.get(**{lookup_field: lookup_value})
                except model.DoesNotExist:
                    raise DjangoPermissionDenied("Object not found") from None

            rule = RuleRegistry.get(rule_name)
            if rule is None:
                raise ValueError(f"Rule '{rule_name}' not found in registry")

            if not rule.check(user, obj):
                raise PermissionDenied(rule_name=rule_name, user=user, obj=obj)

            if inject is not None and obj is not None:
                kwargs[inject] = obj

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
