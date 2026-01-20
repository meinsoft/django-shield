# Django Shield

A simple permission system for Django. Define rules once, protect views with a decorator.


## The Problem

Every Django view needs permission checks:

```python
def edit_post(request, pk):
    post = Post.objects.get(pk=pk)
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    if post.author != request.user:
        return HttpResponseForbidden()
    
    # your code here...
```

You write this in every view. Forget one check? Security hole.

## The Solution

```python
@rule
def is_author(user, post):
    return post.author == user

@guard('is_author', model=Post, lookup='pk')
def edit_post(request, pk):
    # if user is here, they have permission
    ...
```

Define rules once. Use everywhere.

## Installation

```bash
# From GitHub
pip install git+https://github.com/YOUR_USERNAME/django-shield.git

# From source
git clone https://github.com/YOUR_USERNAME/django-shield.git
cd django-shield
pip install -e .
```

## Quick Start

**Step 1:** Define your rules

```python
from django_shield import rule

@rule
def is_author(user, post):
    return post.author == user
```

**Step 2:** Protect your views

```python
from django_shield import guard

@guard('is_author', model=Post, lookup='pk')
def edit_post(request, pk):
    ...
```

**Step 3 (Optional):** Auto-inject objects

```python
@guard('is_author', model=Post, lookup='pk', inject='post')
def edit_post(request, pk, post):
    # post is already fetched, no extra query
    ...
```

## Guard Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `rule_name` | Name of the rule to check | required |
| `model` | Django model class | `None` |
| `lookup` | URL parameter name | `'pk'` |
| `lookup_field` | Model field to query | `'pk'` |
| `inject` | Pass object to view with this name | `None` |

## Current Version: 0.1.0

This is the foundation release with core functionality:

- ✅ `@rule` decorator for defining permission rules
- ✅ `@guard` decorator for protecting function-based views  
- ✅ Object-level permissions
- ✅ Auto-inject fetched objects to views
- ✅ Custom lookup fields (slug, uuid, etc.)

## Roadmap

| Version | Features | Status |
|---------|----------|--------|
| 0.1.0 | Rule & Guard decorators | ✅ Released |
| 0.2.0 | Class-based views, Expression syntax (`'is_admin or is_author'`) | 🔜 Next |
| 0.3.0 | Queryset filtering, SQL compilation | 📋 Planned |
| 0.4.0 | Django REST Framework integration | 📋 Planned |
| 1.0.0 | Async support, Caching, Production ready | 📋 Planned |

## Quality

| Metric | Result |
|--------|--------|
| Test Coverage | 98% |
| Tests | 48 passed |
| Python | 3.10, 3.11, 3.12 |
| Django | 4.2, 5.0, 5.1 |

## Requirements

- Python 3.10+
- Django 4.2+

## License

MIT