# -*- coding: utf-8 -*-
"""
Shop 应用测试基类

提供 shop 模块测试的通用工具和配置，包括：
    - 测试用户创建
    - 测试商品、分类、订单创建
    - API 客户端认证
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from decimal import Decimal

from apps.shop.models import ProductCategory, Product, Cart, Order, Address

User = get_user_model()


class ShopBaseTestCase(TestCase):
    """Shop 测试基类"""

    def setUp(self):
        """每个测试方法执行前的设置"""
        super().setUp()
        cache.clear()

        # 创建 API 客户端
        self.client = APIClient()

        # 创建测试用户
        self.user = self.create_test_user(
            email='shop_test@example.com',
            password='test123456',
            username='shop_tester'
        )

        # 创建第二个用户（用于购物车隔离测试）
        self.user2 = self.create_test_user(
            email='shop_test2@example.com',
            password='test123456',
            username='shop_tester2'
        )

        # 创建测试商品分类
        self.category = self.create_test_category(
            name='魔方商品',
            description='魔方相关商品'
        )

        # 创建测试商品
        self.product = self.create_test_product(
            name='三阶魔方',
            price=Decimal('99.99'),
            stock=100,
            category=self.category
        )

        # 创建第二个商品
        self.product2 = self.create_test_product(
            name='四阶魔方',
            price=Decimal('199.99'),
            stock=50,
            category=self.category
        )

        # 创建测试地址
        self.address = self.create_test_address(user=self.user)

    def tearDown(self):
        """每个测试方法执行后的清理"""
        cache.clear()
        super().tearDown()

    # ============ 辅助方法 ============

    def create_test_user(self, email, password, username, **kwargs):
        """创建普通测试用户"""
        return User.objects.create_user(
            email=email,
            password=password,
            username=username,
            **kwargs
        )

    def create_test_category(self, name='测试分类', parent=None, **kwargs):
        """创建测试商品分类"""
        return ProductCategory.objects.create(
            name=name,
            parent=parent,
            **kwargs
        )

    def create_test_product(self, name='测试商品', price=Decimal('10.00'), stock=100, category=None, **kwargs):
        """创建测试商品"""
        return Product.objects.create(
            name=name,
            price=price,
            stock=stock,
            category=category or self.category,
            **kwargs
        )

    def create_test_cart(self, user=None, product=None, quantity=1, **kwargs):
        """创建测试购物车记录"""
        if user is None:
            user = self.user
        if product is None:
            product = self.product
        return Cart.objects.create(
            user=user,
            product=product,
            quantity=quantity,
            **kwargs
        )

    def create_test_address(self, user=None, name='张三', phone='13800138000', **kwargs):
        """创建测试地址"""
        if user is None:
            user = self.user
        return Address.objects.create(
            user=user,
            name=name,
            phone=phone,
            province='广东省',
            city='深圳市',
            district='南山区',
            detail='科技园路1号',
            **kwargs
        )

    def create_test_order(self, user=None, total_amount=None, status='pending', address=None, **kwargs):
        """创建测试订单"""
        if user is None:
            user = self.user
        if total_amount is None:
            total_amount = self.product.price
        if address is None:
            address = {
                'name': '张三',
                'phone': '13800138000',
                'province': '广东省',
                'city': '深圳市',
                'district': '南山区',
                'detail': '科技园路1号'
            }
        return Order.objects.create(
            user=user,
            order_no=Order.generate_order_no(),
            total_amount=total_amount,
            status=status,
            address=address,
            **kwargs
        )

    def authenticate(self, user=None):
        """认证用户"""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)
        return self.client

    def get_valid_order_data(self, cart_ids=None, address=None):
        """获取有效的订单创建数据"""
        if cart_ids is None:
            # 先创建购物车记录
            cart = self.create_test_cart()
            cart_ids = [cart.id]

        if address is None:
            address = {
                'name': '张三',
                'phone': '13800138000',
                'province': '广东省',
                'city': '深圳市',
                'district': '南山区',
                'detail': '科技园路1号'
            }

        return {
            'cart_ids': cart_ids,
            'address': address
        }


class ShopAPITestCase(ShopBaseTestCase):
    """Shop API 测试基类（自动认证）"""

    def setUp(self):
        super().setUp()
        self.authenticate()
