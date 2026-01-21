from django_shield.conf import is_debug_enabled

PREFIX = "[Django Shield]"


def log_check_start(rule_name):
    if is_debug_enabled():
        print(f"{PREFIX} Checking: {rule_name}")


def log_user(user):
    if is_debug_enabled():
        user_id = getattr(user, "id", None) or getattr(user, "pk", None)
        username = getattr(user, "username", str(user))
        print(f"{PREFIX} User: {username} (id={user_id})")


def log_object(obj):
    if is_debug_enabled():
        if obj is None:
            print(f"{PREFIX} Object: None")
        else:
            model_name = obj.__class__.__name__
            obj_id = getattr(obj, "id", None) or getattr(obj, "pk", None)
            print(f'{PREFIX} Object: {model_name} "{obj}" (id={obj_id})')


def log_rule_result(rule_name, result):
    if is_debug_enabled():
        print(f"{PREFIX} {rule_name} = {result}")


def log_final_result(allowed):
    if is_debug_enabled():
        result = "ALLOWED" if allowed else "DENIED"
        print(f"{PREFIX} Result: {result}")
