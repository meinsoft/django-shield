from django_shield.exceptions import ExpressionEvaluationError
from django_shield.expressions.ast import (
    AndExpr,
    Compare,
    InExpr,
    ListExpr,
    Literal,
    NotExpr,
    ObjAttr,
    OrExpr,
    RuleRef,
    UserAttr,
    UserRef,
)
from django_shield.rules import RuleRegistry


def get_attr_value(obj, path):
    value = obj
    for attr in path:
        if value is None:
            return None
        try:
            value = getattr(value, attr)
        except AttributeError:
            return None
    return value


def evaluate(node, user, obj=None):
    if isinstance(node, RuleRef):
        rule = RuleRegistry.get(node.name)
        if rule is None:
            raise ExpressionEvaluationError(
                "Rule not found",
                detail=f"Rule '{node.name}' is not registered",
            )
        return rule.check(user, obj)

    elif isinstance(node, ObjAttr):
        if obj is None:
            raise ExpressionEvaluationError(
                "Cannot access object attribute",
                detail="Object is None",
            )
        return get_attr_value(obj, node.path)

    elif isinstance(node, UserAttr):
        return get_attr_value(user, node.path)

    elif isinstance(node, UserRef):
        return user

    elif isinstance(node, Literal):
        return node.value

    elif isinstance(node, ListExpr):
        return [evaluate(item, user, obj) for item in node.items]

    elif isinstance(node, Compare):
        left = evaluate(node.left, user, obj)
        right = evaluate(node.right, user, obj)

        if node.op == "==":
            return left == right
        elif node.op == "!=":
            return left != right
        elif node.op == ">":
            return left > right
        elif node.op == "<":
            return left < right
        elif node.op == ">=":
            return left >= right
        elif node.op == "<=":
            return left <= right
        else:
            raise ExpressionEvaluationError(
                "Unknown operator",
                detail=f"Operator '{node.op}' is not supported",
            )

    elif isinstance(node, AndExpr):
        left = evaluate(node.left, user, obj)
        if not left:
            return False
        return bool(evaluate(node.right, user, obj))

    elif isinstance(node, OrExpr):
        left = evaluate(node.left, user, obj)
        if left:
            return True
        return bool(evaluate(node.right, user, obj))

    elif isinstance(node, NotExpr):
        return not evaluate(node.operand, user, obj)

    elif isinstance(node, InExpr):
        left = evaluate(node.left, user, obj)
        right = evaluate(node.right, user, obj)
        return left in right

    else:
        raise ExpressionEvaluationError(
            "Unknown node type",
            detail=f"Cannot evaluate node of type {type(node).__name__}",
        )
