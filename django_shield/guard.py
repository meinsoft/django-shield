import inspect
from functools import wraps

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

from django_shield.debug import (
    log_check_start,
    log_final_result,
    log_object,
    log_user,
)
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


class Guard:
    def __call__(self, rule_name, *, model=None, lookup="pk", lookup_field="pk", inject=None):
        return self._create_decorator([rule_name], model, lookup, lookup_field, inject, mode="single")

    def all(self, *rules, model=None, lookup="pk", lookup_field="pk", inject=None):
        return self._create_decorator(list(rules), model, lookup, lookup_field, inject, mode="all")

    def any(self, *rules, model=None, lookup="pk", lookup_field="pk", inject=None):
        return self._create_decorator(list(rules), model, lookup, lookup_field, inject, mode="any")

    def _create_decorator(self, rules, model, lookup, lookup_field, inject, mode):
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

                allowed, failed_rule = self._check_rules(rules, user, obj, mode)

                if not allowed:
                    raise PermissionDenied(rule_name=failed_rule, user=user, obj=obj)

                if inject is not None and obj is not None:
                    kwargs[inject] = obj

                return view_func(request, *args, **kwargs)

            return wrapper

        def decorate_class(cls):
            original_dispatch = cls.dispatch

            @wraps(original_dispatch)
            def dispatch(self_view, request, *args, **kwargs):
                user = request.user
                obj = None

                if hasattr(self_view, "get_object"):
                    try:
                        obj = self_view.get_object()
                    except Exception:
                        pass

                allowed, failed_rule = self._check_rules(rules, user, obj, mode)

                if not allowed:
                    raise PermissionDenied(rule_name=failed_rule, user=user, obj=obj)

                return original_dispatch(self_view, request, *args, **kwargs)

            cls.dispatch = dispatch
            return cls

        def decorator(view):
            if inspect.isclass(view):
                return decorate_class(view)
            else:
                return decorate_function(view)

        return decorator

    def _check_rules(self, rules, user, obj, mode):
        if mode == "single":
            rule_name = rules[0]
            log_check_start(rule_name)
            log_user(user)
            log_object(obj)
            result = check_permission(rule_name, user, obj)
            log_final_result(result)
            return result, rule_name if not result else None

        elif mode == "all":
            for rule_name in rules:
                log_check_start(rule_name)
                log_user(user)
                log_object(obj)
                result = check_permission(rule_name, user, obj)
                log_final_result(result)
                if not result:
                    return False, rule_name
            return True, None

        elif mode == "any":
            for rule_name in rules:
                log_check_start(rule_name)
                log_user(user)
                log_object(obj)
                result = check_permission(rule_name, user, obj)
                log_final_result(result)
                if result:
                    return True, None
            return False, rules[-1] if rules else None


guard = Guard()
