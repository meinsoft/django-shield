# Expression Syntax

Expression syntax lets you write permission checks inline without defining rule functions.

## What is Expression Syntax?

Instead of creating a rule function:

```python
@rule
def is_author(user, post):
    return post.author == user

@guard('is_author', model=Post)
def edit_post(request, pk):
    ...
```

You can write the check directly:

```python
@guard('obj.author == user', model=Post)
def edit_post(request, pk):
    ...
```

## When to Use Expressions

**Use expressions when:**

- The check is simple (one or two conditions)
- The rule is used in only one place
- You want quick prototyping

**Use named rules when:**

- The logic is complex
- The same check is used in multiple views
- You want to test rules in isolation

## Attribute Access

### Object Attributes

Access object fields with `obj.`:

```python
@guard('obj.status == "published"', model=Post)
def view_post(request, pk):
    ...

@guard('obj.is_active', model=User)
def view_profile(request, user_id):
    ...
```

### Nested Attributes

Chain attributes with dots:

```python
# obj.author.name
@guard('obj.author.name == "admin"', model=Post)

# obj.category.parent.slug
@guard('obj.category.parent.slug == "tech"', model=Article)
```

### User Attributes

Access user fields with `user.`:

```python
@guard('user.is_staff')
def admin_view(request):
    ...

@guard('user.profile.is_verified')
def verified_only(request):
    ...
```

### The user Reference

Use `user` alone to reference the entire user object:

```python
@guard('obj.author == user', model=Post)
def edit_post(request, pk):
    ...

@guard('obj.owner == user', model=Document)
def view_document(request, pk):
    ...
```

## Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `==` | Equal | `obj.status == "active"` |
| `!=` | Not equal | `obj.status != "deleted"` |
| `>` | Greater than | `obj.priority > 5` |
| `<` | Less than | `obj.count < 100` |
| `>=` | Greater or equal | `obj.age >= 18` |
| `<=` | Less or equal | `obj.price <= 1000` |

### Examples

```python
# String comparison
@guard('obj.status == "published"', model=Post)

# Number comparison
@guard('obj.view_count > 1000', model=Article)

# User field comparison
@guard('obj.author.id == user.id', model=Post)
```

## Boolean Operators

### and

Both conditions must be true:

```python
@guard('user.is_authenticated and user.is_active')
def dashboard(request):
    ...

@guard('obj.author == user and obj.status == "draft"', model=Post)
def edit_draft(request, pk):
    ...
```

### or

At least one condition must be true:

```python
@guard('user.is_staff or user.is_superuser')
def admin_area(request):
    ...

@guard('obj.author == user or obj.is_public', model=Document)
def view_document(request, pk):
    ...
```

### not

Negates a condition:

```python
@guard('not user.is_banned')
def post_comment(request):
    ...

@guard('user.is_staff and not obj.is_locked', model=Post)
def edit_post(request, pk):
    ...
```

### Operator Precedence

Precedence from highest to lowest:

1. `not`
2. `and`
3. `or`

This means `a or b and c` is evaluated as `a or (b and c)`.

Use parentheses to change precedence:

```python
# Without parentheses: is_admin or (is_author and is_active)
@guard('is_admin or is_author and is_active')

# With parentheses: (is_admin or is_author) and is_active
@guard('(is_admin or is_author) and is_active')
```

## List Membership with in

Check if a value is in a list:

```python
@guard('obj.status in ["draft", "review"]', model=Post)
def edit_pending(request, pk):
    ...

@guard('obj.priority in [1, 2, 3]', model=Task)
def handle_urgent(request, pk):
    ...

@guard('user.role in ["admin", "moderator", "editor"]')
def manage_content(request):
    ...
```

### Empty Lists

```python
# Always false - nothing is in an empty list
@guard('obj.status in []', model=Post)
```

## Null Comparison

Check for null/None values:

```python
@guard('obj.deleted_at == null', model=Post)
def view_post(request, pk):
    ...

@guard('obj.parent != null', model=Category)
def view_subcategory(request, pk):
    ...
```

You can use `null` or `None`:

```python
# These are equivalent
@guard('obj.deleted_at == null', model=Post)
@guard('obj.deleted_at == None', model=Post)
```

## Literal Values

### Strings

Use double quotes:

```python
@guard('obj.status == "published"', model=Post)
@guard('obj.type == "premium"', model=Account)
```

### Numbers

Integers and floats:

```python
@guard('obj.count > 100', model=Post)
@guard('obj.price <= 99.99', model=Product)
@guard('obj.discount >= 0.5', model=Coupon)
```

Negative numbers:

```python
@guard('obj.balance > -100', model=Account)
```

### Booleans

Use `true`/`false` or `True`/`False`:

```python
@guard('obj.is_active == true', model=User)
@guard('obj.is_featured == True', model=Post)
@guard('user.is_verified == false')
```

## Mixing Rules and Expressions

You can use named rules inside expressions:

```python
@rule
def is_admin(user, obj=None):
    return user.is_superuser

# Mix rule with expression
@guard('is_admin or obj.author == user', model=Post)
def edit_post(request, pk):
    ...
```

## Complex Examples

### Blog Post Access

```python
# View: published or author
@guard('obj.status == "published" or obj.author == user', model=Post)

# Edit: author and not locked
@guard('obj.author == user and not obj.is_locked', model=Post)

# Delete: admin or (author and draft)
@guard('user.is_superuser or (obj.author == user and obj.status == "draft")', model=Post)
```

### E-commerce

```python
# View order: owner or staff
@guard('obj.customer == user or user.is_staff', model=Order)

# Cancel order: owner and pending
@guard('obj.customer == user and obj.status in ["pending", "processing"]', model=Order)

# Refund: staff and not already refunded
@guard('user.is_staff and obj.refund_status == null', model=Order)
```

### Team Collaboration

```python
# View project: member or public
@guard('obj.is_public or user in obj.members', model=Project)

# Edit project: owner or admin role
@guard('obj.owner == user or user.role == "admin"', model=Project)
```

## Error Messages

When an expression has a syntax error, Django Shield shows the error location:

```python
@guard('obj.status == == "draft"', model=Post)  # Syntax error
```

```
ExpressionSyntaxError: Unexpected token '=='
  obj.status == == "draft"
               ^
```

When evaluation fails:

```python
@guard('nonexistent_rule', model=Post)
```

```
ExpressionEvaluationError: Rule not found: Rule 'nonexistent_rule' is not registered
```
