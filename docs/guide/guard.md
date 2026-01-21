# Guard Decorator

The `@guard` decorator protects views by checking permissions before the view runs.

## Basic Usage

```python
from django_shield import guard

@guard('is_authenticated')
def my_view(request):
    # Only authenticated users reach here
    ...
```

If the check fails, Django Shield raises `PermissionDenied` (HTTP 403).

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rule_name` | str | required | Rule name or expression to check |
| `model` | Model | `None` | Django model class to fetch |
| `lookup` | str | `'pk'` | URL parameter name to get lookup value |
| `lookup_field` | str | `'pk'` | Model field to query |
| `inject` | str | `None` | Parameter name to pass object to view |

## Using with Rules

First, define a rule:

```python
from django_shield import rule

@rule
def is_staff(user):
    return user.is_staff
```

Then protect a view:

```python
@guard('is_staff')
def admin_panel(request):
    ...
```

## Using with Expressions

You can use inline expressions instead of named rules:

```python
@guard('user.is_staff')
def admin_panel(request):
    ...

@guard('user.is_authenticated and user.is_active')
def dashboard(request):
    ...
```

## Fetching Objects with `model`

When protecting views that work with specific objects, use the `model` parameter:

```python
from .models import Post

@guard('is_author', model=Post)
def edit_post(request, pk):
    post = Post.objects.get(pk=pk)
    ...
```

Django Shield:

1. Gets `pk` from URL parameters
2. Fetches `Post.objects.get(pk=pk)`
3. Passes the post to your rule
4. Runs the view if allowed

## Custom URL Parameter with `lookup`

If your URL uses a different parameter name:

```python
# URL: /posts/<int:post_id>/edit/
@guard('is_author', model=Post, lookup='post_id')
def edit_post(request, post_id):
    ...
```

## Custom Model Field with `lookup_field`

To query by a field other than `pk`:

```python
# URL: /posts/<slug:slug>/edit/
@guard('is_author', model=Post, lookup='slug', lookup_field='slug')
def edit_post(request, slug):
    ...
```

This runs `Post.objects.get(slug=slug)`.

## Combining lookup and lookup_field

When URL parameter name differs from model field:

```python
# URL: /articles/<str:article_slug>/
@guard('is_author', model=Post, lookup='article_slug', lookup_field='slug')
def edit_post(request, article_slug):
    ...
```

This takes `article_slug` from URL and queries `Post.objects.get(slug=article_slug)`.

## Auto-inject Objects with `inject`

Avoid fetching the object twice:

```python
# Without inject - object fetched twice
@guard('is_author', model=Post)
def edit_post(request, pk):
    post = Post.objects.get(pk=pk)  # Second query
    ...

# With inject - object passed to view
@guard('is_author', model=Post, inject='post')
def edit_post(request, pk, post):
    # 'post' is already fetched, no extra query
    ...
```

The injected object is passed as a keyword argument.

## guard.all() - All Rules Must Pass

Use when every condition must be true:

```python
@guard.all('is_authenticated', 'is_verified', 'is_active')
def secure_action(request):
    ...
```

With objects:

```python
@guard.all('is_team_member', 'has_edit_permission', model=Project)
def edit_project(request, pk):
    ...
```

If any rule fails, the request is denied. The exception includes which rule failed.

## guard.any() - At Least One Rule Must Pass

Use when any condition is sufficient:

```python
@guard.any('is_owner', 'is_admin', 'is_moderator')
def manage_content(request):
    ...
```

With objects:

```python
@guard.any('is_author', 'is_editor', 'is_admin', model=Post)
def edit_post(request, pk):
    ...
```

If all rules fail, the request is denied.

## Error Handling

When permission is denied, Django Shield raises `PermissionDenied`:

```python
from django_shield.exceptions import PermissionDenied

try:
    # Call a guarded view or check manually
    ...
except PermissionDenied as e:
    print(f"Rule failed: {e.rule_name}")
    print(f"User: {e.user}")
    print(f"Object: {e.obj}")
```

The exception contains:

| Attribute | Description |
|-----------|-------------|
| `rule_name` | Name of the failed rule |
| `user` | The user who was denied |
| `obj` | The object (if any) that was checked |

## Handling 404 vs 403

When an object is not found, Django Shield raises Django's `PermissionDenied` (403) instead of `Http404`. This prevents information disclosure about which IDs exist.

To customize this behavior, catch the exception in middleware or use a custom view.

## Complete Examples

### Blog Post Permissions

```python
from django_shield import rule, guard
from .models import Post

@rule
def is_author(user, post):
    return post.author == user

@rule
def is_published(user, post):
    return post.status == 'published'

# Author can edit their posts
@guard('is_author', model=Post, inject='post')
def edit_post(request, pk, post):
    ...

# Anyone can view published posts, author can view their own drafts
@guard.any('is_published', 'is_author', model=Post)
def view_post(request, pk):
    ...

# Only staff can delete
@guard('user.is_staff')
def delete_posts(request):
    ...
```

### E-commerce Order Permissions

```python
from django_shield import rule, guard
from .models import Order

@rule
def is_order_owner(user, order):
    return order.customer == user

@rule
def can_cancel_order(user, order):
    return order.customer == user and order.status == 'pending'

# View own orders
@guard('is_order_owner', model=Order, inject='order')
def view_order(request, order_id, order):
    ...

# Cancel pending orders
@guard('can_cancel_order', model=Order, lookup='order_id')
def cancel_order(request, order_id):
    ...
```
