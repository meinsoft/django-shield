# Class-based Views

Django Shield works with class-based views (CBVs) just like function-based views.

## Basic Usage

Apply `@guard` to the class:

```python
from django.views import View
from django.http import HttpResponse
from django_shield import guard

@guard('user.is_staff')
class AdminDashboard(View):
    def get(self, request):
        return HttpResponse("Admin Dashboard")
```

The decorator wraps the `dispatch` method, so all HTTP methods are protected.

## How It Works

When you decorate a CBV:

1. Django Shield wraps the `dispatch` method
2. Before any request handling, it checks permissions
3. If denied, raises `PermissionDenied`
4. If allowed, continues to `get()`, `post()`, etc.

## Object-level Permissions

### Using get_object()

Django Shield automatically uses your view's `get_object()` method:

```python
from django.views.generic import DetailView
from django_shield import guard, rule
from .models import Post

@rule
def is_author(user, post):
    return post.author == user

@guard('is_author')
class PostEditView(DetailView):
    model = Post

    def get_object(self):
        return Post.objects.get(pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        post = self.get_object()
        # User has permission if they reach here
        ...
```

Django Shield:

1. Calls `get_object()` to get the post
2. Passes it to `is_author(user, post)`
3. Allows or denies based on the result

### With Expression Syntax

```python
@guard('obj.author == user')
class PostEditView(DetailView):
    model = Post

    def get_object(self):
        return Post.objects.get(pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        ...
```

## Views Without Objects

For list views or views without a specific object:

```python
from django.views.generic import ListView
from django_shield import guard

@guard('user.is_authenticated')
class PostListView(ListView):
    model = Post
    template_name = 'posts/list.html'
```

Rules receive `None` as the object:

```python
@rule
def is_premium_user(user, obj=None):
    # obj is None for list views
    return user.subscription.is_active
```

## Generic Views

### DetailView

```python
from django.views.generic import DetailView
from django_shield import guard

@guard('obj.author == user or obj.is_public')
class PostDetailView(DetailView):
    model = Post
    template_name = 'posts/detail.html'
```

### UpdateView

```python
from django.views.generic import UpdateView
from django_shield import guard

@guard('obj.author == user')
class PostUpdateView(UpdateView):
    model = Post
    fields = ['title', 'content']
    template_name = 'posts/edit.html'
```

### DeleteView

```python
from django.views.generic import DeleteView
from django_shield import guard

@guard('obj.author == user or user.is_staff')
class PostDeleteView(DeleteView):
    model = Post
    success_url = '/posts/'
```

### CreateView

Create views don't have an object yet:

```python
from django.views.generic import CreateView
from django_shield import guard

@guard('user.is_authenticated')
class PostCreateView(CreateView):
    model = Post
    fields = ['title', 'content']
```

### ListView

```python
from django.views.generic import ListView
from django_shield import guard

@guard('user.is_staff')
class AllPostsView(ListView):
    model = Post
    template_name = 'posts/admin_list.html'
```

## Combining Multiple Rules

### guard.all()

All rules must pass:

```python
@guard.all('is_authenticated', 'is_verified', 'is_active')
class SecureView(View):
    def get(self, request):
        ...
```

With objects:

```python
@guard.all('is_team_member', 'has_edit_permission')
class ProjectEditView(UpdateView):
    model = Project

    def get_object(self):
        return Project.objects.get(pk=self.kwargs['pk'])
```

### guard.any()

At least one rule must pass:

```python
@guard.any('is_owner', 'is_admin', 'is_editor')
class ContentManageView(View):
    def get(self, request):
        ...
```

## Error Handling in get_object()

If `get_object()` raises an exception, Django Shield continues without an object:

```python
@guard('is_admin')  # Rule only checks user
class SafeView(DetailView):
    model = Post

    def get_object(self):
        # If this fails, permission check runs with obj=None
        raise Http404("Not found")
```

This is useful when you want to check user-level permissions even if the object doesn't exist.

## Complete Example

```python
from django.views.generic import DetailView, UpdateView, DeleteView, ListView
from django_shield import guard, rule
from .models import Post

# Define rules
@rule
def is_author(user, post):
    return post.author == user

@rule
def can_view(user, post):
    return post.is_published or post.author == user

# List all published posts - anyone can view
class PostListView(ListView):
    model = Post
    queryset = Post.objects.filter(is_published=True)

# View single post - must be published or owner
@guard('can_view')
class PostDetailView(DetailView):
    model = Post

# Edit post - must be author
@guard('is_author')
class PostEditView(UpdateView):
    model = Post
    fields = ['title', 'content']

# Delete post - must be author or staff
@guard('obj.author == user or user.is_staff')
class PostDeleteView(DeleteView):
    model = Post
    success_url = '/posts/'

# Admin view - staff only
@guard('user.is_staff')
class PostAdminView(ListView):
    model = Post
    template_name = 'posts/admin.html'
```

## Mixins vs Decorators

You might be used to Django's `LoginRequiredMixin`. Django Shield uses decorators instead of mixins for consistency between function-based and class-based views.

```python
# Django's approach with mixin
class MyView(LoginRequiredMixin, View):
    ...

# Django Shield approach with decorator
@guard('user.is_authenticated')
class MyView(View):
    ...
```

Both approaches work. Use whichever fits your codebase.
