# Blog Application

This example shows how to implement permissions for a typical blog application.

## Models

```python
# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'In Review'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

## Permissions

```python
# permissions.py
from django_shield import rule

# User-level rules
@rule
def is_authenticated(user, obj=None):
    return user.is_authenticated

@rule
def is_staff(user, obj=None):
    return user.is_staff

@rule
def is_editor(user, obj=None):
    return hasattr(user, 'role') and user.role == 'editor'

# Post rules
@rule
def is_post_author(user, post):
    return post.author == user

@rule
def is_post_published(user, post):
    return post.status == 'published'

@rule
def can_view_post(user, post):
    if post.status == 'published':
        return True
    return post.author == user or user.is_staff

@rule
def can_edit_post(user, post):
    if user.is_staff:
        return True
    return post.author == user and post.status in ['draft', 'review']

@rule
def can_delete_post(user, post):
    if user.is_superuser:
        return True
    return post.author == user and post.status == 'draft'

@rule
def can_publish_post(user, post):
    return user.is_staff or (hasattr(user, 'role') and user.role == 'editor')

# Comment rules
@rule
def is_comment_author(user, comment):
    return comment.author == user

@rule
def can_moderate_comment(user, comment):
    return user.is_staff or comment.post.author == user
```

## Views

### Function-based Views

```python
# views.py
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django_shield import guard
from .models import Post, Comment

# Public: List published posts
def post_list(request):
    posts = Post.objects.filter(status='published')
    return render(request, 'blog/post_list.html', {'posts': posts})

# View single post
@guard('can_view_post', model=Post, inject='post')
def post_detail(request, pk, post):
    return render(request, 'blog/post_detail.html', {'post': post})

# Create new post
@guard('is_authenticated')
def post_create(request):
    if request.method == 'POST':
        post = Post.objects.create(
            title=request.POST['title'],
            content=request.POST['content'],
            author=request.user,
            status='draft'
        )
        return redirect('post_detail', pk=post.pk)
    return render(request, 'blog/post_form.html')

# Edit post
@guard('can_edit_post', model=Post, inject='post')
def post_edit(request, pk, post):
    if request.method == 'POST':
        post.title = request.POST['title']
        post.content = request.POST['content']
        post.save()
        return redirect('post_detail', pk=post.pk)
    return render(request, 'blog/post_form.html', {'post': post})

# Delete post
@guard('can_delete_post', model=Post, inject='post')
def post_delete(request, pk, post):
    if request.method == 'POST':
        post.delete()
        return redirect('post_list')
    return render(request, 'blog/post_confirm_delete.html', {'post': post})

# Publish post (staff/editor only)
@guard('can_publish_post', model=Post, inject='post')
def post_publish(request, pk, post):
    post.status = 'published'
    post.save()
    return redirect('post_detail', pk=post.pk)

# Add comment
@guard('is_authenticated')
def comment_create(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    if request.method == 'POST':
        Comment.objects.create(
            post=post,
            author=request.user,
            content=request.POST['content']
        )
        return redirect('post_detail', pk=post_pk)
    return render(request, 'blog/comment_form.html', {'post': post})

# Delete own comment or moderate
@guard.any('is_comment_author', 'can_moderate_comment', model=Comment)
def comment_delete(request, pk):
    comment = Comment.objects.get(pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    return redirect('post_detail', pk=post_pk)

# Approve comment (moderation)
@guard('can_moderate_comment', model=Comment, inject='comment')
def comment_approve(request, pk, comment):
    comment.is_approved = True
    comment.save()
    return redirect('post_detail', pk=comment.post.pk)
```

### Class-based Views

```python
# views.py
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django_shield import guard
from .models import Post

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    queryset = Post.objects.filter(status='published')

@guard('can_view_post')
class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'

@guard('is_authenticated')
class PostCreateView(CreateView):
    model = Post
    fields = ['title', 'content']
    template_name = 'blog/post_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.status = 'draft'
        return super().form_valid(form)

@guard('can_edit_post')
class PostUpdateView(UpdateView):
    model = Post
    fields = ['title', 'content']
    template_name = 'blog/post_form.html'

@guard('can_delete_post')
class PostDeleteView(DeleteView):
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('post_list')
```

## URLs

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('posts/<int:pk>/', views.post_detail, name='post_detail'),
    path('posts/new/', views.post_create, name='post_create'),
    path('posts/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('posts/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('posts/<int:pk>/publish/', views.post_publish, name='post_publish'),
    path('posts/<int:post_pk>/comments/new/', views.comment_create, name='comment_create'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('comments/<int:pk>/approve/', views.comment_approve, name='comment_approve'),
]
```

## Using Expression Syntax

For simpler cases, use expression syntax instead of named rules:

```python
# Instead of defining can_view_post rule
@guard('obj.status == "published" or obj.author == user or user.is_staff', model=Post)
def post_detail(request, pk):
    ...

# Instead of defining can_edit_post rule
@guard('user.is_staff or (obj.author == user and obj.status in ["draft", "review"])', model=Post)
def post_edit(request, pk):
    ...

# Simple checks
@guard('user.is_authenticated')
def post_create(request):
    ...
```

## Permission Summary

| Action | Rule | Who Can Do It |
|--------|------|---------------|
| View published post | Anyone | All visitors |
| View draft post | `can_view_post` | Author, Staff |
| Create post | `is_authenticated` | Logged in users |
| Edit own draft | `can_edit_post` | Author |
| Edit any post | `can_edit_post` | Staff |
| Delete own draft | `can_delete_post` | Author |
| Delete any post | `can_delete_post` | Superuser |
| Publish post | `can_publish_post` | Staff, Editor |
| Delete comment | `is_comment_author` or `can_moderate_comment` | Comment author, Post author, Staff |
| Approve comment | `can_moderate_comment` | Post author, Staff |
