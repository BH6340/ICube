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
    path('orders/notify/', OrderViewSet.as_view({'post': 'notify'}), name='order-notify'),
]