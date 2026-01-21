# API Reference

Complete reference for all Django Shield functions, classes, and exceptions.

## Decorators

### @rule

Register a permission rule function.

```python
from django_shield import rule

@rule
def rule_name(user, obj=None):
    return True  # or False
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | callable | None | The function to decorate |
| `name` | str | None | Custom rule name (defaults to function name) |

**Usage:**

```python
# Basic usage - function name becomes rule name
@rule
def is_author(user, post):
    return post.author == user

# Custom name
@rule(name='can_edit')
def check_edit_permission(user, obj):
    return obj.author == user
```

---

### @guard

Protect a view with permission checks.

```python
from django_shield import guard

@guard(rule_name, model=None, lookup='pk', lookup_field='pk', inject=None)
def view(request, ...):
    ...
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rule_name` | str | required | Rule name or expression to check |
| `model` | Model | None | Django model class to fetch |
| `lookup` | str | `'pk'` | URL parameter name |
| `lookup_field` | str | `'pk'` | Model field to query |
| `inject` | str | None | Parameter name to pass object to view |

**Returns:** Decorated view function or class

**Raises:** `PermissionDenied` if check fails

**Usage:**

```python
# Basic
@guard('is_staff')
def admin_view(request):
    ...

# With model
@guard('is_author', model=Post)
def edit_post(request, pk):
    ...

# With all parameters
@guard('is_author', model=Post, lookup='post_id', lookup_field='id', inject='post')
def edit_post(request, post_id, post):
    ...

# With class-based view
@guard('is_author')
class PostEditView(UpdateView):
    model = Post
```

---

### guard.all()

All rules must pass.

```python
@guard.all(*rules, model=None, lookup='pk', lookup_field='pk', inject=None)
```

**Parameters:** Same as `@guard`

**Usage:**

```python
@guard.all('is_authenticated', 'is_verified', 'is_active')
def secure_view(request):
    ...

@guard.all('is_team_member', 'has_edit_permission', model=Project)
def edit_project(request, pk):
    ...
```

---

### guard.any()

At least one rule must pass.

```python
@guard.any(*rules, model=None, lookup='pk', lookup_field='pk', inject=None)
```

**Parameters:** Same as `@guard`

**Usage:**

```python
@guard.any('is_owner', 'is_admin', 'is_moderator')
def manage_content(request):
    ...
```

---

## Classes

### Rule

Represents a registered permission rule.

```python
from django_shield import Rule
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | str | The rule name |
| `predicate` | callable | The check function |

**Methods:**

#### check(user, obj=None)

Execute the permission check.

```python
rule.check(user, obj)  # Returns True or False
```

---

### RuleRegistry

Registry of all defined rules.

```python
from django_shield import RuleRegistry
```

**Class Methods:**

#### register(rule)

Register a Rule instance.

```python
RuleRegistry.register(rule)
```

#### get(name)

Get a rule by name.

```python
rule = RuleRegistry.get('is_author')  # Returns Rule or None
```

#### exists(name)

Check if a rule is registered.

```python
if RuleRegistry.exists('is_author'):
    ...
```

#### clear()

Remove all registered rules. Useful for testing.

```python
RuleRegistry.clear()
```

---

## Exceptions

### DjangoShieldError

Base exception for all Django Shield errors.

```python
from django_shield import DjangoShieldError
```

---

### PermissionDenied

Raised when a permission check fails.

```python
from django_shield import PermissionDenied
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `rule_name` | str | Name of the failed rule |
| `user` | User | The user who was denied |
| `obj` | object | The object (if any) |

**Usage:**

```python
try:
    # guarded operation
except PermissionDenied as e:
    print(f"Rule: {e.rule_name}")
    print(f"User: {e.user}")
    print(f"Object: {e.obj}")
```

---

### ExpressionSyntaxError

Raised when an expression has invalid syntax.

```python
from django_shield import ExpressionSyntaxError
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `expression` | str | The invalid expression |
| `position` | int | Error position in expression |

---

### ExpressionEvaluationError

Raised when expression evaluation fails.

```python
from django_shield import ExpressionEvaluationError
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `expression` | str | The expression |
| `detail` | str | Error details |

---

## Expression Syntax

### Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal | `obj.status == "active"` |
| `!=` | Not equal | `obj.status != "deleted"` |
| `>` | Greater than | `obj.count > 10` |
| `<` | Less than | `obj.count < 10` |
| `>=` | Greater or equal | `obj.age >= 18` |
| `<=` | Less or equal | `obj.price <= 100` |
| `and` | Logical AND | `a and b` |
| `or` | Logical OR | `a or b` |
| `not` | Logical NOT | `not a` |
| `in` | List membership | `x in [1, 2, 3]` |

### References

| Reference | Description | Example |
|-----------|-------------|---------|
| `obj` | Current object | `obj.author` |
| `obj.field` | Object attribute | `obj.status` |
| `obj.a.b` | Nested attribute | `obj.author.name` |
| `user` | Current user | `obj.author == user` |
| `user.field` | User attribute | `user.is_staff` |

### Literals

| Type | Example |
|------|---------|
| String | `"active"` |
| Integer | `42`, `-5` |
| Float | `3.14`, `-0.5` |
| Boolean | `true`, `false`, `True`, `False` |
| Null | `null`, `None` |
| List | `[1, 2, 3]`, `["a", "b"]` |

### Precedence

From highest to lowest:

1. Parentheses `()`
2. Attribute access `.`
3. Comparison `==`, `!=`, `>`, `<`, `>=`, `<=`
4. `in`
5. `not`
6. `and`
7. `or`

---

## Settings

Configure Django Shield in `settings.py`:

```python
DJANGO_SHIELD = {
    'DEBUG': False,  # Enable debug logging
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `DEBUG` | bool | `False` | Enable debug output |

---

## Module Exports

```python
from django_shield import (
    # Decorators
    rule,
    guard,

    # Classes
    Rule,
    RuleRegistry,

    # Exceptions
    DjangoShieldError,
    PermissionDenied,
    ExpressionSyntaxError,
    ExpressionEvaluationError,
)
```
