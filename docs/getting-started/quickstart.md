# Quick Start

This guide shows you how to protect Django views in 5 minutes.

## Step 1: Create a Rule

A rule is a function that returns `True` if the user has permission.

Create a file called `permissions.py` in your app:

```python
from django_shield import rule

@rule
def is_author(user, post):
    """Check if user is the author of the post."""
    return post.author == user
```

The `@rule` decorator registers this function. The function name becomes the rule name.

## Step 2: Protect a View

Use the `@guard` decorator to protect your view:

```python
from django_shield import guard
from .models import Post

@guard('is_author', model=Post, lookup='pk')
def edit_post(request, pk):
    post = Post.objects.get(pk=pk)
    # User has permission if they reach here
    return render(request, 'posts/edit.html', {'post': post})
```

What happens:

1. Django Shield fetches the `Post` using `pk` from the URL
2. It calls `is_author(request.user, post)`
3. If `True`, the view runs
4. If `False`, it raises `PermissionDenied`

## Step 3: Use Expression Syntax

For simple checks, you can skip creating a rule function:

```python
@guard('obj.author == user', model=Post)
def edit_post(request, pk):
    ...
```

Or combine multiple conditions:

```python
@guard('obj.author == user or user.is_staff', model=Post)
def edit_post(request, pk):
    ...
```

## Step 4: Test in Browser

1. Make sure your rule file is imported (add it to your app's `__init__.py` or import in `views.py`)

2. Create a URL pattern:

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('posts/<int:pk>/edit/', views.edit_post, name='edit_post'),
]
```

3. Try to access a post you own - it works
4. Try to access a post you don't own - you get 403 Forbidden

## Step 5: Auto-inject Objects

Avoid fetching the object twice by using `inject`:

```python
@guard('is_author', model=Post, lookup='pk', inject='post')
def edit_post(request, pk, post):
    # 'post' is passed automatically, no extra query needed
    return render(request, 'posts/edit.html', {'post': post})
```

## Complete Example

```python
# permissions.py
from django_shield import rule

@rule
def is_author(user, post):
    return post.author == user

@rule
def is_staff(user):
    return user.is_staff
```

```python
# views.py
from django_shield import guard
from .models import Post

# Only post author can edit
@guard('is_author', model=Post, inject='post')
def edit_post(request, pk, post):
    ...

# Only staff can delete
@guard('is_staff')
def delete_all_posts(request):
    ...

# Author or staff can view drafts
@guard('obj.author == user or user.is_staff', model=Post)
def view_draft(request, pk):
    ...
```

## Next Steps

- [Rules](../guide/rules.md) - Learn all about defining rules
- [Guard Decorator](../guide/guard.md) - All `@guard` options explained
- [Expression Syntax](../guide/expressions.md) - Write inline permission checks
