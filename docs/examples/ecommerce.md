# E-commerce Application

This example shows how to implement permissions for an e-commerce platform.

## Models

```python
# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Store(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores')
    is_active = models.BooleanField(default=True)

class Product(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=False)

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
```

## Permissions

```python
# permissions.py
from django_shield import rule

# Store permissions
@rule
def is_store_owner(user, store):
    return store.owner == user

@rule
def is_store_staff(user, store):
    return user in store.staff.all() if hasattr(store, 'staff') else False

@rule
def can_manage_store(user, store):
    return store.owner == user or user.is_staff

# Product permissions
@rule
def can_view_product(user, product):
    if product.is_published:
        return True
    return product.store.owner == user

@rule
def can_edit_product(user, product):
    return product.store.owner == user or user.is_staff

# Order permissions
@rule
def is_order_customer(user, order):
    return order.customer == user

@rule
def is_order_seller(user, order):
    return order.store.owner == user

@rule
def can_view_order(user, order):
    return order.customer == user or order.store.owner == user or user.is_staff

@rule
def can_cancel_order(user, order):
    if order.status not in ['pending', 'paid']:
        return False
    return order.customer == user

@rule
def can_update_order_status(user, order):
    return order.store.owner == user or user.is_staff

@rule
def can_refund_order(user, order):
    if order.status not in ['paid', 'shipped', 'delivered']:
        return False
    return user.is_staff or order.store.owner == user

# Review permissions
@rule
def can_write_review(user, product):
    # Check if user has purchased this product
    from .models import Order
    return Order.objects.filter(
        customer=user,
        store=product.store,
        status='delivered'
    ).exists()

@rule
def is_review_author(user, review):
    return review.customer == user

@rule
def can_delete_review(user, review):
    return review.customer == user or review.product.store.owner == user or user.is_staff
```

## Views

```python
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django_shield import guard
from .models import Store, Product, Order, Review

# Store management
@guard('is_store_owner', model=Store, inject='store')
def store_dashboard(request, store_id, store):
    products = store.products.all()
    orders = store.orders.all()[:10]
    return render(request, 'ecommerce/store_dashboard.html', {
        'store': store,
        'products': products,
        'orders': orders
    })

@guard('can_manage_store', model=Store, inject='store')
def store_settings(request, store_id, store):
    if request.method == 'POST':
        store.name = request.POST['name']
        store.save()
        return redirect('store_dashboard', store_id=store.pk)
    return render(request, 'ecommerce/store_settings.html', {'store': store})

# Product management
@guard('can_view_product', model=Product, inject='product')
def product_detail(request, pk, product):
    return render(request, 'ecommerce/product_detail.html', {'product': product})

@guard('is_store_owner', model=Store, lookup='store_id', inject='store')
def product_create(request, store_id, store):
    if request.method == 'POST':
        product = Product.objects.create(
            store=store,
            name=request.POST['name'],
            price=request.POST['price'],
            stock=request.POST['stock']
        )
        return redirect('product_detail', pk=product.pk)
    return render(request, 'ecommerce/product_form.html', {'store': store})

@guard('can_edit_product', model=Product, inject='product')
def product_edit(request, pk, product):
    if request.method == 'POST':
        product.name = request.POST['name']
        product.price = request.POST['price']
        product.stock = request.POST['stock']
        product.save()
        return redirect('product_detail', pk=product.pk)
    return render(request, 'ecommerce/product_form.html', {'product': product})

# Order management
@guard('can_view_order', model=Order, inject='order')
def order_detail(request, order_id, order):
    return render(request, 'ecommerce/order_detail.html', {'order': order})

@guard('is_order_customer', model=Order, lookup='order_id')
def order_list(request):
    orders = Order.objects.filter(customer=request.user)
    return render(request, 'ecommerce/order_list.html', {'orders': orders})

@guard('can_cancel_order', model=Order, lookup='order_id', inject='order')
def order_cancel(request, order_id, order):
    order.status = 'cancelled'
    order.save()
    return redirect('order_detail', order_id=order.pk)

@guard('can_update_order_status', model=Order, lookup='order_id', inject='order')
def order_ship(request, order_id, order):
    if order.status == 'paid':
        order.status = 'shipped'
        order.save()
    return redirect('order_detail', order_id=order.pk)

@guard('can_refund_order', model=Order, lookup='order_id', inject='order')
def order_refund(request, order_id, order):
    order.status = 'refunded'
    order.save()
    # Process refund logic here
    return redirect('order_detail', order_id=order.pk)

# Seller's order management
@guard('is_order_seller', model=Order, lookup='order_id', inject='order')
def seller_order_detail(request, order_id, order):
    return render(request, 'ecommerce/seller_order_detail.html', {'order': order})

# Reviews
@guard('can_write_review', model=Product, lookup='product_id', inject='product')
def review_create(request, product_id, product):
    if request.method == 'POST':
        Review.objects.create(
            product=product,
            customer=request.user,
            rating=request.POST['rating'],
            comment=request.POST['comment'],
            is_verified_purchase=True
        )
        return redirect('product_detail', pk=product.pk)
    return render(request, 'ecommerce/review_form.html', {'product': product})

@guard('can_delete_review', model=Review, inject='review')
def review_delete(request, pk, review):
    product_pk = review.product.pk
    review.delete()
    return redirect('product_detail', pk=product_pk)
```

## Expression Syntax Examples

```python
# Simple owner check
@guard('obj.store.owner == user', model=Product)
def product_edit(request, pk):
    ...

# Status-based permission
@guard('obj.status in ["pending", "paid"] and obj.customer == user', model=Order)
def order_cancel(request, order_id):
    ...

# Multiple conditions
@guard('obj.customer == user or obj.store.owner == user or user.is_staff', model=Order)
def order_detail(request, order_id):
    ...

# Staff override
@guard('user.is_staff or obj.store.owner == user', model=Product)
def product_edit(request, pk):
    ...
```

## URLs

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Store management
    path('stores/<int:store_id>/', views.store_dashboard, name='store_dashboard'),
    path('stores/<int:store_id>/settings/', views.store_settings, name='store_settings'),

    # Products
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('stores/<int:store_id>/products/new/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),

    # Orders (customer)
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.order_cancel, name='order_cancel'),

    # Orders (seller)
    path('seller/orders/<int:order_id>/', views.seller_order_detail, name='seller_order_detail'),
    path('seller/orders/<int:order_id>/ship/', views.order_ship, name='order_ship'),
    path('seller/orders/<int:order_id>/refund/', views.order_refund, name='order_refund'),

    # Reviews
    path('products/<int:product_id>/reviews/new/', views.review_create, name='review_create'),
    path('reviews/<int:pk>/delete/', views.review_delete, name='review_delete'),
]
```

## Permission Summary

| Action | Rule | Who Can Do It |
|--------|------|---------------|
| View store dashboard | `is_store_owner` | Store owner |
| Manage store settings | `can_manage_store` | Store owner, Admin |
| View published product | Anyone | All visitors |
| View unpublished product | `can_view_product` | Store owner |
| Create product | `is_store_owner` | Store owner |
| Edit product | `can_edit_product` | Store owner, Admin |
| View own order | `is_order_customer` | Customer |
| View order as seller | `is_order_seller` | Store owner |
| Cancel order | `can_cancel_order` | Customer (if pending/paid) |
| Ship order | `can_update_order_status` | Store owner, Admin |
| Refund order | `can_refund_order` | Store owner, Admin |
| Write review | `can_write_review` | Verified purchasers |
| Delete review | `can_delete_review` | Reviewer, Store owner, Admin |
