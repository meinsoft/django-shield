from django_shield.rules import Rule, RuleRegistry, rule

from .conftest import MockUser


class TestRule:
    def test_stores_name(self) -> None:
        r = Rule(name="test_rule", predicate=lambda u: True)
        assert r.name == "test_rule"

    def test_stores_predicate(self) -> None:
        def predicate(u: MockUser) -> bool:
            return True

        r = Rule(name="test_rule", predicate=predicate)
        assert r.predicate is predicate

    def test_check_without_obj_calls_predicate_with_user_only(self) -> None:
        call_args: list = []

        def predicate(user: MockUser) -> bool:
            call_args.append(user)
            return True

        r = Rule(name="test", predicate=predicate)
        user = MockUser()
        r.check(user)

        assert len(call_args) == 1
        assert call_args[0] is user

    def test_check_with_obj_calls_predicate_with_user_and_obj(self) -> None:
        call_args: list = []

        def predicate(user: MockUser, obj: object) -> bool:
            call_args.append((user, obj))
            return True

        r = Rule(name="test", predicate=predicate)
        user = MockUser()
        obj = {"id": 1}
        r.check(user, obj)

        assert len(call_args) == 1
        assert call_args[0] == (user, obj)

    def test_check_returns_true_when_predicate_returns_true(self) -> None:
        r = Rule(name="test", predicate=lambda u: True)
        assert r.check(MockUser()) is True

    def test_check_returns_false_when_predicate_returns_false(self) -> None:
        r = Rule(name="test", predicate=lambda u: False)
        assert r.check(MockUser()) is False

    def test_check_with_complex_predicate(self) -> None:
        def is_staff(user: MockUser) -> bool:
            return user.is_staff

        r = Rule(name="is_staff", predicate=is_staff)

        regular_user = MockUser(is_staff=False)
        staff_user = MockUser(is_staff=True)

        assert r.check(regular_user) is False
        assert r.check(staff_user) is True


class TestRuleRegistry:
    def test_register_stores_rule(self) -> None:
        r = Rule(name="test_rule", predicate=lambda u: True)
        RuleRegistry.register(r)
        assert RuleRegistry.get("test_rule") is r

    def test_get_returns_none_for_unknown_rule(self) -> None:
        assert RuleRegistry.get("nonexistent") is None

    def test_exists_returns_true_for_registered_rule(self) -> None:
        r = Rule(name="test_rule", predicate=lambda u: True)
        RuleRegistry.register(r)
        assert RuleRegistry.exists("test_rule") is True

    def test_exists_returns_false_for_unknown_rule(self) -> None:
        assert RuleRegistry.exists("nonexistent") is False

    def test_clear_removes_all_rules(self) -> None:
        RuleRegistry.register(Rule(name="rule1", predicate=lambda u: True))
        RuleRegistry.register(Rule(name="rule2", predicate=lambda u: True))

        RuleRegistry.clear()

        assert RuleRegistry.exists("rule1") is False
        assert RuleRegistry.exists("rule2") is False

    def test_register_overwrites_existing_rule(self) -> None:
        r1 = Rule(name="test", predicate=lambda u: True)
        r2 = Rule(name="test", predicate=lambda u: False)

        RuleRegistry.register(r1)
        RuleRegistry.register(r2)

        assert RuleRegistry.get("test") is r2


class TestRuleDecorator:
    def test_decorator_without_arguments(self) -> None:
        @rule
        def can_view(user: MockUser) -> bool:
            return True

        assert RuleRegistry.exists("can_view")
        registered_rule = RuleRegistry.get("can_view")
        assert registered_rule is not None
        assert registered_rule.name == "can_view"

    def test_decorator_with_custom_name(self) -> None:
        @rule(name="custom_rule_name")
        def my_function(user: MockUser) -> bool:
            return True

        assert RuleRegistry.exists("custom_rule_name")
        assert not RuleRegistry.exists("my_function")

    def test_decorator_returns_original_function(self) -> None:
        @rule
        def original_func(user: MockUser) -> bool:
            return True

        assert callable(original_func)
        assert original_func.__name__ == "original_func"

    def test_decorated_function_is_still_callable(self) -> None:
        @rule
        def is_authenticated(user: MockUser) -> bool:
            return user.id is not None

        user = MockUser(id=1)
        assert is_authenticated(user) is True

    def test_multiple_rules_can_be_registered(self) -> None:
        @rule
        def rule_one(user: MockUser) -> bool:
            return True

        @rule
        def rule_two(user: MockUser) -> bool:
            return False

        @rule(name="custom_name")
        def rule_three(user: MockUser) -> bool:
            return True

        assert RuleRegistry.exists("rule_one")
        assert RuleRegistry.exists("rule_two")
        assert RuleRegistry.exists("custom_name")

    def test_rule_predicate_is_the_decorated_function(self) -> None:
        @rule
        def can_edit(user: MockUser) -> bool:
            return user.is_staff

        registered_rule = RuleRegistry.get("can_edit")
        assert registered_rule is not None
        assert registered_rule.check(MockUser(is_staff=True)) is True
        assert registered_rule.check(MockUser(is_staff=False)) is False
