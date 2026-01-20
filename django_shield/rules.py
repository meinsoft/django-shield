class Rule:
    def __init__(self, name, predicate):
        self.name = name
        self.predicate = predicate

    def check(self, user, obj=None):
        if obj is None:
            return self.predicate(user)
        return self.predicate(user, obj)


class RuleRegistry:
    _rules = {}

    @classmethod
    def register(cls, rule):
        cls._rules[rule.name] = rule

    @classmethod
    def get(cls, name):
        return cls._rules.get(name)

    @classmethod
    def exists(cls, name):
        return name in cls._rules

    @classmethod
    def clear(cls):
        cls._rules.clear()


def rule(func=None, *, name=None):
    def decorator(fn):
        rule_name = name or fn.__name__
        r = Rule(rule_name, fn)
        RuleRegistry.register(r)
        return fn

    if func is not None:
        return decorator(func)
    return decorator
