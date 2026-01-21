from sly import Lexer

from django_shield.exceptions import ExpressionSyntaxError


class ShieldLexer(Lexer):
    tokens = {
        AND,
        OR,
        NOT,
        IN,
        TRUE,
        FALSE,
        NULL,
        OBJ,
        USER,
        EQ,
        NE,
        GE,
        LE,
        GT,
        LT,
        STRING,
        NUMBER,
        NAME,
        DOT,
        LPAREN,
        RPAREN,
        LBRACKET,
        RBRACKET,
        COMMA,
    }

    ignore = " \t"

    EQ = r"=="
    NE = r"!="
    GE = r">="
    LE = r"<="
    GT = r">"
    LT = r"<"
    DOT = r"\."
    LPAREN = r"\("
    RPAREN = r"\)"
    LBRACKET = r"\["
    RBRACKET = r"\]"
    COMMA = r","

    @_(r'"[^"]*"')
    def STRING(self, t):
        t.value = t.value[1:-1]
        return t

    @_(r"-?\d+\.\d+")
    def NUMBER(self, t):
        t.value = float(t.value)
        return t

    @_(r"-?\d+")
    def NUMBER_INT(self, t):
        t.type = "NUMBER"
        t.value = int(t.value)
        return t

    NAME = r"[a-zA-Z_][a-zA-Z0-9_]*"

    NAME["and"] = AND
    NAME["or"] = OR
    NAME["not"] = NOT
    NAME["in"] = IN
    NAME["true"] = TRUE
    NAME["True"] = TRUE
    NAME["false"] = FALSE
    NAME["False"] = FALSE
    NAME["null"] = NULL
    NAME["None"] = NULL
    NAME["obj"] = OBJ
    NAME["user"] = USER

    def error(self, t):
        raise ExpressionSyntaxError(
            f"Invalid character '{t.value[0]}'",
            expression=self.text,
            position=t.index,
        )
