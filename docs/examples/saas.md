# Multi-tenant SaaS Application

This example shows how to implement permissions for a multi-tenant SaaS application with organizations, teams, and role-based access.

## Models

```python
# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_orgs')
    plan = models.CharField(max_length=20, default='free')  # free, pro, enterprise
    created_at = models.DateTimeField(auto_now_add=True)

class Membership(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'organization']

class Project(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')

class Document(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
```

## Permissions

```python
# permissions.py
from django_shield import rule
from .models import Membership

def get_membership(user, organization):
    """Helper to get user's membership in an organization."""
    try:
        return Membership.objects.get(user=user, organization=organization)
    except Membership.DoesNotExist:
        return None

def get_user_role(user, organization):
    """Get user's role in organization."""
    membership = get_membership(user, organization)
    return membership.role if membership else None

# Organization permissions
@rule
def is_org_member(user, org):
    return Membership.objects.filter(user=user, organization=org).exists()

@rule
def is_org_admin(user, org):
    role = get_user_role(user, org)
    return role in ['owner', 'admin']

@rule
def is_org_owner(user, org):
    return org.owner == user

@rule
def can_manage_org(user, org):
    return org.owner == user or user.is_superuser

@rule
def can_invite_members(user, org):
    role = get_user_role(user, org)
    return role in ['owner', 'admin']

@rule
def can_remove_members(user, org):
    role = get_user_role(user, org)
    return role in ['owner', 'admin']

# Project permissions
@rule
def can_view_project(user, project):
    if project.is_archived:
        role = get_user_role(user, project.organization)
        return role in ['owner', 'admin']
    return is_org_member.predicate(user, project.organization)

@rule
def can_edit_project(user, project):
    role = get_user_role(user, project.organization)
    return role in ['owner', 'admin', 'member']

@rule
def can_delete_project(user, project):
    role = get_user_role(user, project.organization)
    return role in ['owner', 'admin']

@rule
def can_archive_project(user, project):
    role = get_user_role(user, project.organization)
    return role in ['owner', 'admin']

# Task permissions
@rule
def can_view_task(user, task):
    return is_org_member.predicate(user, task.project.organization)

@rule
def can_edit_task(user, task):
    role = get_user_role(user, task.project.organization)
    if role == 'viewer':
        return False
    return True

@rule
def can_assign_task(user, task):
    role = get_user_role(user, task.project.organization)
    return role in ['owner', 'admin', 'member']

@rule
def is_task_assignee(user, task):
    return task.assignee == user

# Document permissions
@rule
def can_view_document(user, document):
    if document.is_public:
        return True
    return is_org_member.predicate(user, document.project.organization)

@rule
def can_edit_document(user, document):
    role = get_user_role(user, document.project.organization)
    return role in ['owner', 'admin', 'member']

@rule
def can_delete_document(user, document):
    if document.created_by == user:
        return True
    role = get_user_role(user, document.project.organization)
    return role in ['owner', 'admin']

# Plan-based permissions
@rule
def has_pro_plan(user, org):
    return org.plan in ['pro', 'enterprise']

@rule
def has_enterprise_plan(user, org):
    return org.plan == 'enterprise'

@rule
def can_use_advanced_features(user, org):
    return org.plan in ['pro', 'enterprise'] and is_org_member.predicate(user, org)
```

## Views

```python
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django_shield import guard
from .models import Organization, Project, Task, Document, Membership

# Organization views
@guard('is_org_member', model=Organization, lookup='org_slug', lookup_field='slug', inject='org')
def org_dashboard(request, org_slug, org):
    projects = org.projects.filter(is_archived=False)
    return render(request, 'saas/org_dashboard.html', {
        'org': org,
        'projects': projects
    })

@guard('can_manage_org', model=Organization, lookup='org_slug', lookup_field='slug', inject='org')
def org_settings(request, org_slug, org):
    if request.method == 'POST':
        org.name = request.POST['name']
        org.save()
        return redirect('org_dashboard', org_slug=org.slug)
    return render(request, 'saas/org_settings.html', {'org': org})

@guard('can_invite_members', model=Organization, lookup='org_slug', lookup_field='slug', inject='org')
def member_invite(request, org_slug, org):
    if request.method == 'POST':
        # Invite logic here
        ...
    return render(request, 'saas/member_invite.html', {'org': org})

@guard('is_org_admin', model=Organization, lookup='org_slug', lookup_field='slug', inject='org')
def member_list(request, org_slug, org):
    members = org.memberships.select_related('user')
    return render(request, 'saas/member_list.html', {
        'org': org,
        'members': members
    })

# Project views
@guard('can_view_project', model=Project, inject='project')
def project_detail(request, pk, project):
    tasks = project.tasks.all()
    documents = project.documents.all()
    return render(request, 'saas/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'documents': documents
    })

@guard('is_org_member', model=Organization, lookup='org_slug', lookup_field='slug', inject='org')
def project_create(request, org_slug, org):
    role = get_user_role(request.user, org)
    if role == 'viewer':
        raise PermissionDenied("Viewers cannot create projects")

    if request.method == 'POST':
        project = Project.objects.create(
            organization=org,
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            created_by=request.user
        )
        return redirect('project_detail', pk=project.pk)
    return render(request, 'saas/project_form.html', {'org': org})

@guard('can_edit_project', model=Project, inject='project')
def project_edit(request, pk, project):
    if request.method == 'POST':
        project.name = request.POST['name']
        project.description = request.POST.get('description', '')
        project.save()
        return redirect('project_detail', pk=project.pk)
    return render(request, 'saas/project_form.html', {'project': project})

@guard('can_archive_project', model=Project, inject='project')
def project_archive(request, pk, project):
    project.is_archived = True
    project.save()
    return redirect('org_dashboard', org_slug=project.organization.slug)

# Task views
@guard('can_view_task', model=Task, inject='task')
def task_detail(request, pk, task):
    return render(request, 'saas/task_detail.html', {'task': task})

@guard('can_edit_project', model=Project, lookup='project_pk', inject='project')
def task_create(request, project_pk, project):
    if request.method == 'POST':
        task = Task.objects.create(
            project=project,
            title=request.POST['title'],
            description=request.POST.get('description', ''),
            created_by=request.user
        )
        return redirect('task_detail', pk=task.pk)
    return render(request, 'saas/task_form.html', {'project': project})

@guard('can_edit_task', model=Task, inject='task')
def task_edit(request, pk, task):
    if request.method == 'POST':
        task.title = request.POST['title']
        task.description = request.POST.get('description', '')
        task.save()
        return redirect('task_detail', pk=task.pk)
    return render(request, 'saas/task_form.html', {'task': task})

@guard.any('is_task_assignee', 'can_assign_task', model=Task, inject='task')
def task_complete(request, pk, task):
    task.is_completed = True
    task.save()
    return redirect('task_detail', pk=task.pk)

# Document views
@guard('can_view_document', model=Document, inject='document')
def document_detail(request, pk, document):
    return render(request, 'saas/document_detail.html', {'document': document})

@guard('can_edit_document', model=Document, inject='document')
def document_edit(request, pk, document):
    if request.method == 'POST':
        document.title = request.POST['title']
        document.content = request.POST['content']
        document.save()
        return redirect('document_detail', pk=document.pk)
    return render(request, 'saas/document_form.html', {'document': document})

@guard('can_delete_document', model=Document, inject='document')
def document_delete(request, pk, document):
    project_pk = document.project.pk
    document.delete()
    return redirect('project_detail', pk=project_pk)

# Plan-based feature gates
@guard.all('is_org_member', 'has_pro_plan', model=Organization, lookup='org_slug', lookup_field='slug')
def advanced_analytics(request, org_slug):
    # Pro feature
    ...

@guard.all('is_org_admin', 'has_enterprise_plan', model=Organization, lookup='org_slug', lookup_field='slug')
def sso_settings(request, org_slug):
    # Enterprise feature
    ...
```

## Expression Syntax Examples

```python
# Role-based checks with helper
@guard('is_org_admin', model=Organization, lookup='org_slug', lookup_field='slug')
def admin_panel(request, org_slug):
    ...

# Owner check
@guard('obj.owner == user', model=Organization, lookup='org_slug', lookup_field='slug')
def org_billing(request, org_slug):
    ...

# Plan-based feature with membership check
@guard.all('is_org_member', 'has_pro_plan', model=Organization)
def pro_feature(request, pk):
    ...
```

## URLs

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Organization
    path('orgs/<slug:org_slug>/', views.org_dashboard, name='org_dashboard'),
    path('orgs/<slug:org_slug>/settings/', views.org_settings, name='org_settings'),
    path('orgs/<slug:org_slug>/members/', views.member_list, name='member_list'),
    path('orgs/<slug:org_slug>/members/invite/', views.member_invite, name='member_invite'),

    # Projects
    path('orgs/<slug:org_slug>/projects/new/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/archive/', views.project_archive, name='project_archive'),

    # Tasks
    path('projects/<int:project_pk>/tasks/new/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/complete/', views.task_complete, name='task_complete'),

    # Documents
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),

    # Plan-gated features
    path('orgs/<slug:org_slug>/analytics/', views.advanced_analytics, name='advanced_analytics'),
    path('orgs/<slug:org_slug>/sso/', views.sso_settings, name='sso_settings'),
]
```

## Role Hierarchy

| Role | Permissions |
|------|-------------|
| **Owner** | Full access, billing, delete org |
| **Admin** | Manage members, all projects/tasks |
| **Member** | Create/edit projects and tasks |
| **Viewer** | Read-only access |

## Permission Summary

| Action | Required Role/Condition |
|--------|-------------------------|
| View org dashboard | Any member |
| Manage org settings | Owner only |
| Invite members | Owner, Admin |
| Remove members | Owner, Admin |
| Create project | Owner, Admin, Member |
| Edit project | Owner, Admin, Member |
| Delete/archive project | Owner, Admin |
| View task | Any member |
| Edit task | Owner, Admin, Member |
| Complete task | Assignee, or Admin+ |
| View document | Member, or public |
| Edit document | Owner, Admin, Member |
| Delete document | Creator, or Admin+ |
| Advanced analytics | Pro plan members |
| SSO settings | Enterprise Admins |
