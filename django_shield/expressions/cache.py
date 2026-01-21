from django_shield.expressions.parser import parse_expression

_cache = {}


def get_or_parse(expr_string):
    if expr_string not in _cache:
        _cache[expr_string] = parse_expression(expr_string)
    return _cache[expr_string]


def clear_cache():
    _cache.clear()
