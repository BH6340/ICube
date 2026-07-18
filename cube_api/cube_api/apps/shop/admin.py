from django.contrib import admin
from .models import ProductCategory, Product, Cart, Order, OrderItem


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'sort_order', 'created_at']
    list_filter = ['parent']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_on_sale', 'sales_count', 'created_at']
    list_filter = ['category', 'is_on_sale']
    search_fields = ['name']
    list_editable = ['price', 'stock', 'is_on_sale']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'created_at']
    list_filter = ['user']
    search_fields = ['product__name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['order_no', 'user__username']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'price', 'quantity']
    list_filter = ['order__status']
    search_fields = ['product__name']