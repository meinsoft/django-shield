from typing import Any


class DjangoShieldError(Exception):
    pass


class PermissionDenied(DjangoShieldError):
    def __init__(
        self,
        rule_name: str,
        user: Any,
        obj: Any = None,
    ) -> None:
        self.rule_name = rule_name
        self.user = user
        self.obj = obj

        if obj is not None:
            message = (
                f"User '{user}' does not have permission '{rule_name}' "
                f"for object '{obj}'"
            )
        else:
            message = f"User '{user}' does not have permission '{rule_name}'"

        super().__init__(message)
