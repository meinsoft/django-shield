import inspect
from functools import wraps

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

from django_shield.exceptions import PermissionDenied
from django_shield.expressions import evaluate, get_or_parse
from django_shield.rules import RuleRegistry


def check_permission(rule_name, user, obj=None):
    if RuleRegistry.exists(rule_name):
        rule = RuleRegistry.get(rule_name)
        return rule.check(user, obj)
    else:
        expr = get_or_parse(rule_name)
        return evaluate(expr, user, obj)


def guard(rule_name, *, model=None, lookup="pk", lookup_field="pk", inject=None):
    def decorate_function(view_func):
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

            if not check_permission(rule_name, user, obj):
                raise PermissionDenied(rule_name=rule_name, user=user, obj=obj)

            if inject is not None and obj is not None:
                kwargs[inject] = obj

            return view_func(request, *args, **kwargs)

        return wrapper

    def decorate_class(cls):
        original_dispatch = cls.dispatch

        @wraps(original_dispatch)
        def dispatch(self, request, *args, **kwargs):
            user = request.user
            obj = None

            if hasattr(self, "get_object"):
                try:
                    obj = self.get_object()
                except Exception:
                    pass

            if not check_permission(rule_name, user, obj):
                raise PermissionDenied(rule_name=rule_name, user=user, obj=obj)

            return original_dispatch(self, request, *args, **kwargs)

        cls.dispatch = dispatch
        return cls

    def decorator(view):
        if inspect.isclass(view):
            return decorate_class(view)
        else:
            return decorate_function(view)

    return decorator
