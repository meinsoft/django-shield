class DjangoShieldError(Exception):
    pass


class PermissionDenied(DjangoShieldError):
    def __init__(self, rule_name, user, obj=None):
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


class ExpressionSyntaxError(DjangoShieldError):
    def __init__(self, message, expression=None, position=None):
        self.expression = expression
        self.position = position

        if expression and position is not None:
            pointer = " " * position + "^"
            full_message = f"{message}\n  {expression}\n  {pointer}"
        elif expression:
            full_message = f"{message}\n  {expression}"
        else:
            full_message = message

        super().__init__(full_message)


class ExpressionEvaluationError(DjangoShieldError):
    def __init__(self, message, expression=None, detail=None):
        self.expression = expression
        self.detail = detail

        if expression and detail:
            full_message = f"{message}: {detail}\n  Expression: {expression}"
        elif expression:
            full_message = f"{message}\n  Expression: {expression}"
        elif detail:
            full_message = f"{message}: {detail}"
        else:
            full_message = message

        super().__init__(full_message)
