# Rules

Rules are the core building blocks of Django Shield. A rule is a function that checks if a user has permission.

## What is a Rule?

A rule is a Python function that:

- Takes `user` as the first parameter
- Optionally takes an object as the second parameter
- Returns `True` (allowed) or `False` (denied)

## The @rule Decorator

Use `@rule` to register a permission function:

```python
from django_shield import rule

@rule
def is_authenticated(user):
    return user.is_authenticated
```

The function name becomes the rule name. You can use this name with `@guard`:

```python
@guard('is_authenticated')
def my_view(request):
    ...
```

## Rules Without Object

Some rules only need the user:

```python
@rule
def is_staff(user):
    return user.is_staff

@rule
def is_superuser(user):
    return user.is_superuser

@rule
def is_verified(user):
    return user.email_verified
```

Use these for views that don't operate on a specific object:

```python
@guard('is_staff')
def admin_dashboard(request):
    ...
```

## Rules With Object

Most rules check if a user can access a specific object:

```python
@rule
def is_author(user, post):
    return post.author == user

@rule
def can_view_document(user, document):
    return document.is_public or document.owner == user

@rule
def is_team_member(user, project):
    return user in project.team.members.all()
```

Use with the `model` parameter:

```python
@guard('is_author', model=Post)
def edit_post(request, pk):
    ...
```

## Custom Rule Names

By default, the function name is the rule name. Use `name` to set a custom name:

```python
@rule(name='can_edit')
def check_edit_permission(user, obj):
    return obj.author == user or user.is_staff
```

Now use `'can_edit'` instead of `'check_edit_permission'`:

```python
@guard('can_edit', model=Post)
def edit_view(request, pk):
    ...
```

## Accessing Rules from Registry

You can access registered rules programmatically:

```python
from django_shield import RuleRegistry

# Check if a rule exists
if RuleRegistry.exists('is_author'):
    rule = RuleRegistry.get('is_author')
    result = rule.check(user, post)
```

## Combining Rules

### Using guard.all()

All rules must pass:

```python
@guard.all('is_authenticated', 'is_verified', 'is_active')
def secure_view(request):
    ...
```

### Using guard.any()

At least one rule must pass:

```python
@guard.any('is_author', 'is_staff', 'is_superuser')
def edit_post(request, pk):
    ...
```

### Combining in Expression Syntax

Use `and`, `or`, `not`:

```python
@guard('is_author or is_staff')
def edit_post(request, pk):
    ...

@guard('is_authenticated and not is_banned')
def post_comment(request):
    ...
```

## Best Practices

### 1. Keep Rules Simple

Each rule should check one thing:

```python
# Good - single responsibility
@rule
def is_author(user, post):
    return post.author == user

@rule
def is_staff(user):
    return user.is_staff

# Use together
@guard.any('is_author', 'is_staff', model=Post)
```

```python
# Avoid - too many responsibilities
@rule
def can_edit(user, post):
    if user.is_superuser:
        return True
    if user.is_staff:
        return True
    if post.author == user:
        return True
    if user in post.editors.all():
        return True
    return False
```

### 2. Name Rules Clearly

Use descriptive names that explain the permission:

```python
# Good
@rule
def is_project_owner(user, project):
    ...

@rule
def can_view_draft(user, post):
    ...

# Avoid
@rule
def check(user, obj):
    ...

@rule
def perm1(user):
    ...
```

### 3. Handle None Objects

When a rule might receive `None`:

```python
@rule
def can_edit_post(user, post):
    if post is None:
        return False
    return post.author == user
```

### 4. Organize Rules by Domain

Group related rules in dedicated files:

```
myapp/
    permissions/
        __init__.py
        posts.py      # Post-related rules
        users.py      # User-related rules
        teams.py      # Team-related rules
```

Import all rules in `__init__.py`:

```python
# permissions/__init__.py
from .posts import *
from .users import *
from .teams import *
```

### 5. Import Rules Early

Rules must be imported before views use them. Import in your app's `apps.py`:

```python
# apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'myapp'

    def ready(self):
        import myapp.permissions  # Register all rules
```
