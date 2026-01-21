class Expr:
    pass


class RuleRef(Expr):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"RuleRef({self.name!r})"

    def __eq__(self, other):
        return isinstance(other, RuleRef) and self.name == other.name


class ObjAttr(Expr):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return f"ObjAttr({self.path!r})"

    def __eq__(self, other):
        return isinstance(other, ObjAttr) and self.path == other.path


class UserAttr(Expr):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return f"UserAttr({self.path!r})"

    def __eq__(self, other):
        return isinstance(other, UserAttr) and self.path == other.path


class Literal(Expr):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Literal({self.value!r})"

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value


class ListExpr(Expr):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return f"ListExpr({self.items!r})"

    def __eq__(self, other):
        return isinstance(other, ListExpr) and self.items == other.items


class Compare(Expr):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"Compare({self.left!r}, {self.op!r}, {self.right!r})"

    def __eq__(self, other):
        return (
            isinstance(other, Compare)
            and self.left == other.left
            and self.op == other.op
            and self.right == other.right
        )


class AndExpr(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"AndExpr({self.left!r}, {self.right!r})"

    def __eq__(self, other):
        return (
            isinstance(other, AndExpr)
            and self.left == other.left
            and self.right == other.right
        )


class OrExpr(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"OrExpr({self.left!r}, {self.right!r})"

    def __eq__(self, other):
        return (
            isinstance(other, OrExpr)
            and self.left == other.left
            and self.right == other.right
        )


class NotExpr(Expr):
    def __init__(self, operand):
        self.operand = operand

    def __repr__(self):
        return f"NotExpr({self.operand!r})"

    def __eq__(self, other):
        return isinstance(other, NotExpr) and self.operand == other.operand


class InExpr(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"InExpr({self.left!r}, {self.right!r})"

    def __eq__(self, other):
        return (
            isinstance(other, InExpr)
            and self.left == other.left
            and self.right == other.right
        )


class UserRef(Expr):
    def __repr__(self):
        return "UserRef()"

    def __eq__(self, other):
        return isinstance(other, UserRef)
