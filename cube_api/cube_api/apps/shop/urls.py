# -*- coding: utf-8 -*-
"""
商城模块路由配置

定义商城模块的 API 路由，包括：
    - 商品分类：/api/shop/categories/
    - 商品：/api/shop/products/
    - 购物车：/api/shop/cart/
    - 订单：/api/shop/orders/
    - 订单支付：/api/shop/orders/{pk}/pay/
    - 订单取消：/api/shop/orders/{pk}/cancel/
    - 订单确认：/api/shop/orders/{pk}/complete/

设计特点：
    - **标准视图集路由**：使用 DefaultRouter 自动生成 CRUD 路由
    - **自定义动作路由**：pay、cancel、complete 通过额外 path 定义
    - **支付宝回调**：通过 viewset 的 action 装饰器定义，无需手动路由
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductCategoryViewSet, ProductViewSet, CartViewSet, OrderViewSet

router = DefaultRouter()
router.register('categories', ProductCategoryViewSet)
router.register('products', ProductViewSet)
router.register('cart', CartViewSet)
router.register('orders', OrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('orders/<int:pk>/pay/', OrderViewSet.as_view({'put': 'pay'}), name='order-pay'),
    path('orders/<int:pk>/cancel/', OrderViewSet.as_view({'put': 'cancel'}), name='order-cancel'),
    path('orders/<int:pk>/complete/', OrderViewSet.as_view({'put': 'complete'}), name='order-complete'),
]