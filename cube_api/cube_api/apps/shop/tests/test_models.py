# -*- coding: utf-8 -*-
"""
Shop 模块模型测试

测试 shop 模块的核心模型，包括：
    - ProductCategory: 商品分类
    - Product: 商品
    - Cart: 购物车
    - Order/OrderItem: 订单与订单明细
    - Address: 收货地址
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from decimal import Decimal

from apps.shop.models import ProductCategory, Product, Cart, Order, OrderItem, Address

User = get_user_model()


class ProductCategoryModelTest(TestCase):
    """商品分类模型测试"""

    def setUp(self):
        self.category = ProductCategory.objects.create(
            name='测试分类',
            description='测试描述'
        )

    def test_create_category_success(self):
        """测试创建分类成功"""
        self.assertEqual(self.category.name, '测试分类')
        self.assertEqual(self.category.description, '测试描述')
        self.assertIsNone(self.category.parent)

    def test_category_str_method(self):
        """测试 __str__ 方法"""
        self.assertEqual(str(self.category), '测试分类')

    def test_sub_category(self):
        """测试子分类"""
        sub = ProductCategory.objects.create(
            name='子分类',
            parent=self.category
        )
        self.assertEqual(sub.parent, self.category)
        self.assertIn(sub, self.category.children.all())

    def test_category_ordering(self):
        """测试分类排序"""
        ProductCategory.objects.create(name='B分类', sort_order=2)
        ProductCategory.objects.create(name='A分类', sort_order=1)

        categories = ProductCategory.objects.all()
        self.assertEqual(categories[0].name, 'A分类')
        self.assertEqual(categories[1].name, 'B分类')


class ProductModelTest(TestCase):
    """商品模型测试"""

    def setUp(self):
        self.category = ProductCategory.objects.create(name='测试分类')
        self.product = Product.objects.create(
            name='测试商品',
            price=Decimal('99.99'),
            stock=100,
            category=self.category
        )

    def test_create_product_success(self):
        """测试创建商品成功"""
        self.assertEqual(self.product.name, '测试商品')
        self.assertEqual(self.product.price, Decimal('99.99'))
        self.assertEqual(self.product.stock, 100)
        self.assertTrue(self.product.is_on_sale)

    def test_product_str_method(self):
        """测试 __str__ 方法"""
        self.assertEqual(str(self.product), '测试商品')

    def test_product_default_values(self):
        """测试默认值"""
        self.assertEqual(self.product.sales_count, 0)
        self.assertIsNone(self.product.original_price)

    def test_product_not_on_sale(self):
        """测试商品下架"""
        self.product.is_on_sale = False
        self.product.save()
        self.assertFalse(self.product.is_on_sale)


class CartModelTest(TestCase):
    """购物车模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='cart@example.com',
            password='testpass',
            username='cartuser'
        )
        self.product = Product.objects.create(
            name='购物车商品',
            price=Decimal('50.00'),
            stock=10
        )

    def test_create_cart_success(self):
        """测试创建购物车记录"""
        cart = Cart.objects.create(
            user=self.user,
            product=self.product,
            quantity=2
        )
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.product, self.product)
        self.assertEqual(cart.quantity, 2)

    def test_cart_str_method(self):
        """测试 __str__ 方法"""
        cart = Cart.objects.create(
            user=self.user,
            product=self.product,
            quantity=1
        )
        self.assertIn('cartuser', str(cart))
        self.assertIn('购物车商品', str(cart))

    def test_cart_default_quantity(self):
        """测试默认数量为 1"""
        cart = Cart.objects.create(
            user=self.user,
            product=self.product
        )
        self.assertEqual(cart.quantity, 1)


class OrderModelTest(TestCase):
    """订单模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='order@example.com',
            password='testpass',
            username='orderuser'
        )

    def test_create_order_success(self):
        """测试创建订单成功"""
        order = Order.objects.create(
            user=self.user,
            order_no=Order.generate_order_no(),
            total_amount=Decimal('100.00'),
            address={'name': '张三', 'phone': '13800138000', 'province': '广东省', 'city': '深圳市', 'district': '南山区', 'detail': '科技园路1号'}
        )

        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, 'pending')
        self.assertIsNotNone(order.order_no)
        self.assertTrue(order.order_no.startswith('ORD'))

    def test_order_str_method(self):
        """测试 __str__ 方法"""
        order = Order.objects.create(
            user=self.user,
            order_no='ORD20240101000000ABC12345',
            total_amount=Decimal('50.00'),
            address={'name': '张三', 'phone': '13800138000', 'province': '广东省', 'city': '深圳市', 'district': '南山区', 'detail': '科技园路1号'}
        )
        self.assertEqual(str(order), 'ORD20240101000000ABC12345')

    def test_generate_order_no_uniqueness(self):
        """测试订单号唯一性"""
        order_nos = set()
        for _ in range(100):
            order_no = Order.generate_order_no()
            self.assertNotIn(order_no, order_nos)
            order_nos.add(order_no)

    def test_order_status_flow(self):
        """测试订单状态流转"""
        order = Order.objects.create(
            user=self.user,
            order_no=Order.generate_order_no(),
            total_amount=Decimal('100.00'),
            address={'name': '张三', 'phone': '13800138000', 'province': '广东省', 'city': '深圳市', 'district': '南山区', 'detail': '科技园路1号'}
        )

        # 初始状态为待付款
        self.assertEqual(order.status, 'pending')

        # 手动更新状态
        order.status = 'paid'
        order.save()
        self.assertEqual(order.status, 'paid')

        order.status = 'shipped'
        order.save()
        self.assertEqual(order.status, 'shipped')

        order.status = 'completed'
        order.save()
        self.assertEqual(order.status, 'completed')

    def test_order_status_cancelled(self):
        """测试订单取消状态"""
        order = Order.objects.create(
            user=self.user,
            order_no=Order.generate_order_no(),
            total_amount=Decimal('100.00'),
            address={'name': '张三', 'phone': '13800138000', 'province': '广东省', 'city': '深圳市', 'district': '南山区', 'detail': '科技园路1号'}
        )

        order.status = 'cancelled'
        order.save()
        self.assertEqual(order.status, 'cancelled')

    def test_order_no_unique(self):
        """测试订单号唯一性约束"""
        order_no = Order.generate_order_no()
        Order.objects.create(
            user=self.user,
            order_no=order_no,
            total_amount=Decimal('100.00'),
            address={'name': '张三', 'phone': '13800138000', 'province': '广东省', 'city': '深圳市', 'district': '南山区', 'detail': '科技园路1号'}
        )

        with self.assertRaises(IntegrityError):
            Order.objects.create(
                user=self.user,
                order_no=order_no,
                total_amount=Decimal('50.00'),
                address={'name': '李四', 'phone': '13900139000', 'province': '北京市', 'city': '北京市', 'district': '朝阳区', 'detail': '建国路88号'}
            )


class OrderItemModelTest(TestCase):
    """订单明细模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='orderitem@example.com',
            password='testpass',
            username='orderitemuser'
        )
        self.product = Product.objects.create(
            name='订单商品',
            price=Decimal('25.00'),
            stock=100
        )
        self.order = Order.objects.create(
            user=self.user,
            order_no=Order.generate_order_no(),
            total_amount=Decimal('50.00'),
            address={'name': '张三', 'phone': '13800138000', 'province': '广东省', 'city': '深圳市', 'district': '南山区', 'detail': '科技园路1号'}
        )

    def test_create_order_item_success(self):
        """测试创建订单明细"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=Decimal('25.00'),
            quantity=2
        )

        self.assertEqual(item.order, self.order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.price, Decimal('25.00'))
        self.assertEqual(item.quantity, 2)

    def test_order_item_str_method(self):
        """测试 __str__ 方法"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            price=Decimal('25.00'),
            quantity=1
        )
        self.assertIn(str(self.order), str(item))
        self.assertIn('订单商品', str(item))

    def test_order_items_relation(self):
        """测试订单与明细的一对多关系"""
        OrderItem.objects.create(order=self.order, product=self.product, price=Decimal('25.00'), quantity=1)
        OrderItem.objects.create(order=self.order, product=self.product, price=Decimal('25.00'), quantity=2)

        self.assertEqual(self.order.items.count(), 2)


class AddressModelTest(TestCase):
    """收货地址模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='address@example.com',
            password='testpass',
            username='addressuser'
        )

    def test_create_address_success(self):
        """测试创建地址成功"""
        address = Address.objects.create(
            user=self.user,
            name='张三',
            phone='13800138000',
            province='广东省',
            city='深圳市',
            district='南山区',
            detail='科技园路1号'
        )

        self.assertEqual(address.user, self.user)
        self.assertEqual(address.name, '张三')
        self.assertEqual(address.phone, '13800138000')
        self.assertFalse(address.is_default)

    def test_address_str_method(self):
        """测试 __str__ 方法"""
        address = Address.objects.create(
            user=self.user,
            name='张三',
            phone='13800138000',
            province='广东省',
            city='深圳市',
            district='南山区',
            detail='科技园路1号'
        )
        self.assertIn('张三', str(address))
        self.assertIn('13800138000', str(address))

    def test_address_full_address_property(self):
        """测试 full_address 属性"""
        address = Address.objects.create(
            user=self.user,
            name='张三',
            phone='13800138000',
            province='广东省',
            city='深圳市',
            district='南山区',
            detail='科技园路1号'
        )
        self.assertEqual(address.full_address, '广东省深圳市南山区科技园路1号')

    def test_address_default(self):
        """测试默认地址"""
        address = Address.objects.create(
            user=self.user,
            name='默认用户',
            phone='13800138000',
            province='北京市',
            city='北京市',
            district='朝阳区',
            detail='建国路88号',
            is_default=True
        )
        self.assertTrue(address.is_default)
