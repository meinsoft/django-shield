# Django Shield

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-4.2%2B-green)](https://www.djangoproject.com/)
[![Coverage](https://img.shields.io/badge/coverage-96%25-brightgreen)]()
[![Tests](https://img.shields.io/badge/tests-192%20passed-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Declarative permission system for Django.** Define rules once, protect views with a decorator.

```python
@guard('obj.author == user or user.is_staff')
def edit_post(request, pk):
    ...
```

No more repetitive permission checks. No more forgotten security holes.

---

## Why Django Shield?

Django's built-in permissions are great for model-level access, but fall short for object-level permissions. You end up writing the same checks in every view:

```python
# ❌ The old way - repetitive and error-prone
def edit_post(request, pk):
    post = Post.objects.get(pk=pk)
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    if post.author != request.user and not request.user.is_staff:
        raise PermissionDenied
    
    # Finally, your actual code...
```

**Forget one check? Security hole.** Write it 50 times? DRY violation.

```python
# ✅ The Django Shield way - clean and secure
@guard('obj.author == user or user.is_staff')
def edit_post(request, pk):
    # If we're here, permission is granted
    ...
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Expression Syntax** | Write rules as readable strings: `'is_admin or obj.author == user'` |
| **@guard Decorator** | One decorator protects your entire view |
| **CBV Support** | Works with both function-based and class-based views |
| **Object Injection** | Auto-fetch and inject objects into your views |
| **Rule Registry** | Define complex rules once, reuse everywhere |
| **Zero DB Overhead** | No permission tables, no bloat |
| **Full Operators** | `and`, `or`, `not`, `==`, `!=`, `>`, `<`, `>=`, `<=`, `in` |

---

## Installation

```bash
pip install git+https://github.com/meinsoft/django-shield.git
```

No configuration needed. No middleware. No apps to add.

---

## Quick Start

### Basic Usage

```python
from django_shield import guard

# Protect with a simple expression
@guard('user.is_authenticated')
def dashboard(request):
    return render(request, 'dashboard.html')

# Object-level permission
@guard('obj.author == user', model=Post, lookup='pk')
def edit_post(request, pk):
    post = Post.objects.get(pk=pk)
    return render(request, 'edit.html', {'post': post})

# Complex logic in one line
@guard('obj.author == user or user.is_staff')
def delete_post(request, pk):
    ...
```

### Auto-inject Objects

Skip the extra query. Let Django Shield fetch and inject the object:

```python
@guard('obj.author == user', model=Post, lookup='pk', inject='post')
def edit_post(request, pk, post):
    # 'post' is already fetched and permission-checked
    return render(request, 'edit.html', {'post': post})
```

### Class-Based Views

```python
from django.views.generic import UpdateView, DeleteView

@guard('obj.author == user or user.is_staff')
class PostUpdateView(UpdateView):
    model = Post
    fields = ['title', 'content']

@guard('user.is_staff')
class PostDeleteView(DeleteView):
    model = Post
    success_url = '/posts/'
```

---

## Expression Syntax

Django Shield understands a powerful expression language:

### Attribute Access

```python
# User attributes
@guard('user.is_authenticated')
@guard('user.is_staff')
@guard('user.profile.is_premium')

# Object attributes
@guard('obj.is_published')
@guard('obj.status == "draft"')
@guard('obj.author.is_active')
```

### Comparisons

```python
@guard('obj.status == "published"')
@guard('obj.status != "archived"')
@guard('obj.view_count > 100')
@guard('obj.priority <= 3')
@guard('obj.author == user')  # Compare objects
@guard('obj.deleted_at == null')  # Null checks
```

### Boolean Logic

```python
@guard('user.is_staff or user.is_superuser')
@guard('obj.is_published and obj.is_active')
@guard('not obj.is_locked')
@guard('user.is_staff or (obj.author == user and obj.status == "draft")')
```

### List Membership

```python
@guard('obj.status in ["draft", "pending", "review"]')
@guard('user.role in ["admin", "editor", "moderator"]')
```

---

## Reusable Rules

For complex permission logic, define reusable rules:

```python
from django_shield import rule, guard

@rule
def is_premium_user(user):
    return (
        user.is_authenticated and 
        user.subscription.is_active and 
        user.subscription.plan in ['premium', 'enterprise']
    )

@rule
def can_access_analytics(user, report):
    if user.is_staff:
        return True
    if report.owner == user:
        return True
    return report.shared_with.filter(id=user.id).exists()

# Use in guards
@guard('is_premium_user')
def premium_dashboard(request):
    ...

@guard('can_access_analytics', model=Report, lookup='pk')
def view_report(request, pk):
    ...

# Combine rules with expressions
@guard('is_premium_user and obj.is_published')
def view_premium_content(request, pk):
    ...
```

---

## API Reference

### @guard Decorator

```python
@guard(
    rule_name,              # Rule name or expression string
    model=None,             # Django model class (optional)
    lookup='pk',            # URL parameter name (default: 'pk')
    lookup_field='pk',      # Model field to query (default: 'pk')
    inject=None             # Inject object as this parameter (optional)
)
```

### @rule Decorator

```python
@rule                       # Uses function name as rule name
def is_author(user, obj):
    return obj.author == user

@rule(name='custom_name')   # Custom rule name
def my_rule(user, obj):
    return True
```

### Exceptions

```python
from django_shield import PermissionDenied, ExpressionSyntaxError

# PermissionDenied - raised when permission check fails
# Attributes: rule_name, user, obj

# ExpressionSyntaxError - raised for invalid expressions
```

---

## Examples

### Blog Application

```python
# rules.py
from django_shield import rule

@rule
def is_author(user, post):
    return post.author == user

@rule
def is_editor(user):
    return user.groups.filter(name='editors').exists()

@rule
def can_publish(user, post):
    return user.is_staff or (is_author(user, post) and is_editor(user))
```

```python
# views.py
from django_shield import guard

@guard('user.is_authenticated')
def post_list(request):
    posts = Post.objects.filter(is_published=True)
    return render(request, 'posts/list.html', {'posts': posts})

@guard('is_author or is_editor', model=Post, lookup='pk', inject='post')
def edit_post(request, pk, post):
    # post is already fetched
    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'posts/edit.html', {'form': form, 'post': post})

@guard('can_publish', model=Post, lookup='pk')
def publish_post(request, pk):
    post = Post.objects.get(pk=pk)
    post.is_published = True
    post.save()
    return redirect('post_detail', pk=pk)

@guard('obj.author == user or user.is_staff', model=Post, lookup='pk')
def delete_post(request, pk):
    Post.objects.filter(pk=pk).delete()
    return redirect('post_list')
```

### E-commerce Application

```python
@guard('user.is_authenticated')
def cart(request):
    ...

@guard('obj.user == user', model=Order, lookup='order_id', lookup_field='id')
def order_detail(request, order_id):
    ...

@guard('obj.user == user and obj.status == "pending"', model=Order, lookup='pk')
def cancel_order(request, pk):
    ...

@guard('user.is_staff or obj.vendor.owner == user', model=Product, lookup='slug', lookup_field='slug')
def edit_product(request, slug):
    ...
```

### Multi-tenant SaaS

```python
@rule
def belongs_to_tenant(user, obj):
    return obj.tenant_id == user.tenant_id

@rule
def is_tenant_admin(user):
    return user.role == 'admin' and user.tenant is not None

@guard('belongs_to_tenant', model=Project, lookup='pk')
def view_project(request, pk):
    ...

@guard('belongs_to_tenant and is_tenant_admin', model=Settings, lookup='pk')
def edit_settings(request, pk):
    ...
```

---

## Comparison with Alternatives

| Feature | django-guardian | django-rules | Django Shield |
|---------|----------------|--------------|---------------|
| Object-level permissions | ✅ | ✅ | ✅ |
| No database tables | ❌ | ✅ | ✅ |
| Expression syntax | ❌ | ❌ | ✅ |
| @guard decorator | ❌ | ❌ | ✅ |
| Object injection | ❌ | ❌ | ✅ |
| CBV decorator support | ❌ | ❌ | ✅ |
| Combine rules inline | ❌ | ❌ | ✅ |

---

## Requirements

- Python 3.10+
- Django 4.2+

---

## Roadmap

| Version | Features | Status |
|---------|----------|--------|
| 0.1.0 | @rule, @guard, inject | ✅ Released |
| 0.2.0 | CBV support, Expression syntax | ✅ Released |
| 0.3.0 | SQL compilation, Queryset filtering | 🔜 Coming |
| 0.4.0 | Django REST Framework integration | 📋 Planned |
| 1.0.0 | Async support, Caching | 📋 Planned |

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Links

- [GitHub Repository](https://github.com/meinsoft/django-shield)
- [Issue Tracker](https://github.com/meinsoft/django-shield/issues)
- [Changelog](https://github.com/meinsoft/django-shield/releases)

---

<p align="center">
  Made with ❤️ for the Django community
</p>
