# Django Shield

A declarative permission system for Django. Define rules once, protect views with a decorator.

Django Shield removes the need to write permission checks in every view. You define rules as simple Python functions, then use the `@guard` decorator to protect your views.

## Key Features

| Feature | Description |
|---------|-------------|
| **Expression Syntax** | Write permissions inline: `'obj.author == user'` |
| **@guard Decorator** | Protect views with a single line |
| **CBV Support** | Works with class-based views |
| **Zero DB Overhead** | No database tables or migrations |
| **Debug Mode** | See exactly why permissions pass or fail |

## Before and After

**Without Django Shield:**

```python
def edit_post(request, pk):
    post = Post.objects.get(pk=pk)

    if not request.user.is_authenticated:
        return redirect('login')

    if post.author != request.user and not request.user.is_staff:
        raise PermissionDenied()

    # Your view code here...
```

**With Django Shield:**

```python
@guard('obj.author == user or user.is_staff', model=Post)
def edit_post(request, pk):
    # If user reaches here, they have permission
    ...
```

Or define reusable rules:

```python
@rule
def can_edit_post(user, post):
    return post.author == user or user.is_staff

@guard('can_edit_post', model=Post)
def edit_post(request, pk):
    ...
```

## Quick Example

```python
from django_shield import rule, guard

# Define a rule
@rule
def is_author(user, post):
    return post.author == user

# Protect a view
@guard('is_author', model=Post, lookup='pk')
def edit_post(request, pk):
    post = Post.objects.get(pk=pk)
    # User has permission if they reach here
    ...
```

## Next Steps

- [Installation](getting-started/installation.md) - Install Django Shield
- [Quick Start](getting-started/quickstart.md) - Build your first protected view
- [GitHub Repository](https://github.com/meinsoft/django-shield) - Source code and issues
