from sly import Parser

from django_shield.exceptions import ExpressionSyntaxError
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
from django_shield.expressions.lexer import ShieldLexer


class ShieldParser(Parser):
    tokens = ShieldLexer.tokens
    debugfile = None

    precedence = (
        ("left", OR),
        ("left", AND),
        ("right", NOT),
        ("left", IN),
        ("left", EQ, NE, GT, LT, GE, LE),
        ("left", DOT),
    )

    def __init__(self):
        self._expression_text = None

    @_("expr OR expr")
    def expr(self, p):
        return OrExpr(p.expr0, p.expr1)

    @_("expr AND expr")
    def expr(self, p):
        return AndExpr(p.expr0, p.expr1)

    @_("NOT expr")
    def expr(self, p):
        return NotExpr(p.expr)

    @_("expr IN list_expr")
    def expr(self, p):
        return InExpr(p.expr, p.list_expr)

    @_("expr EQ expr")
    def expr(self, p):
        return Compare(p.expr0, "==", p.expr1)

    @_("expr NE expr")
    def expr(self, p):
        return Compare(p.expr0, "!=", p.expr1)

    @_("expr GT expr")
    def expr(self, p):
        return Compare(p.expr0, ">", p.expr1)

    @_("expr LT expr")
    def expr(self, p):
        return Compare(p.expr0, "<", p.expr1)

    @_("expr GE expr")
    def expr(self, p):
        return Compare(p.expr0, ">=", p.expr1)

    @_("expr LE expr")
    def expr(self, p):
        return Compare(p.expr0, "<=", p.expr1)

    @_("LPAREN expr RPAREN")
    def expr(self, p):
        return p.expr

    @_("obj_attr")
    def expr(self, p):
        return p.obj_attr

    @_("user_attr")
    def expr(self, p):
        return p.user_attr

    @_("user_ref")
    def expr(self, p):
        return p.user_ref

    @_("literal")
    def expr(self, p):
        return p.literal

    @_("rule_ref")
    def expr(self, p):
        return p.rule_ref

    @_("OBJ DOT attr_path")
    def obj_attr(self, p):
        return ObjAttr(p.attr_path)

    @_("USER DOT attr_path")
    def user_attr(self, p):
        return UserAttr(p.attr_path)

    @_("USER")
    def user_ref(self, p):
        return UserRef()

    @_("attr_path DOT NAME")
    def attr_path(self, p):
        return p.attr_path + [p.NAME]

    @_("NAME")
    def attr_path(self, p):
        return [p.NAME]

    @_("STRING")
    def literal(self, p):
        return Literal(p.STRING)

    @_("NUMBER")
    def literal(self, p):
        return Literal(p.NUMBER)

    @_("TRUE")
    def literal(self, p):
        return Literal(True)

    @_("FALSE")
    def literal(self, p):
        return Literal(False)

    @_("NULL")
    def literal(self, p):
        return Literal(None)

    @_("NAME")
    def rule_ref(self, p):
        return RuleRef(p.NAME)

    @_("LBRACKET list_items RBRACKET")
    def list_expr(self, p):
        return ListExpr(p.list_items)

    @_("LBRACKET RBRACKET")
    def list_expr(self, p):
        return ListExpr([])

    @_("list_items COMMA expr")
    def list_items(self, p):
        return p.list_items + [p.expr]

    @_("expr")
    def list_items(self, p):
        return [p.expr]

    def error(self, token):
        if token:
            raise ExpressionSyntaxError(
                f"Unexpected token '{token.value}'",
                expression=self._expression_text,
                position=token.index,
            )
        else:
            raise ExpressionSyntaxError(
                "Unexpected end of expression",
                expression=self._expression_text,
            )


def parse_expression(text):
    lexer = ShieldLexer()
    parser = ShieldParser()
    parser._expression_text = text
    lexer.text = text
    tokens = lexer.tokenize(text)
    result = parser.parse(tokens)
    if result is None:
        raise ExpressionSyntaxError(
            "Failed to parse expression",
            expression=text,
        )
    return result
