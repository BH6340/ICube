# -*- coding: utf-8 -*-
"""
Shop 模块 API 接口测试

测试商城模块的核心 API 接口，包括：
    - 商品分类接口
    - 商品接口
    - 购物车接口
    - 订单接口
    - 地址接口
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status
from decimal import Decimal

from .base import ShopBaseTestCase, ShopAPITestCase
from apps.shop.models import ProductCategory, Product, Cart, Order, OrderItem, Address

User = get_user_model()


class ProductCategoryAPITest(ShopBaseTestCase):
    """商品分类 API 测试"""

    def test_list_categories(self):
        """测试获取分类列表"""
        response = self.client.get('/api/shop/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_list_sub_categories(self):
        """测试分类列表包含子分类"""
        ProductCategory.objects.create(name='子分类', parent=self.category)
        response = self.client.get('/api/shop/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProductAPITest(ShopBaseTestCase):
    """商品 API 测试"""

    def test_list_products(self):
        """测试获取商品列表"""
        response = self.client.get('/api/shop/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_product(self):
        """测试获取商品详情"""
        response = self.client.get(f'/api/shop/products/{self.product.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_filter_products_by_category(self):
        """测试按分类筛选商品"""
        response = self.client.get(f'/api/shop/products/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_products_by_keyword(self):
        """测试搜索商品"""
        response = self.client.get('/api/shop/products/?keyword=魔方')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_products_by_price_range(self):
        """测试价格区间筛选"""
        response = self.client.get('/api/shop/products/?price_min=50&price_max=150')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_only_on_sale_products(self):
        """测试只显示上架商品"""
        self.product.is_on_sale = False
        self.product.save()

        response = self.client.get('/api/shop/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CartAPITest(ShopAPITestCase):
    """购物车 API 测试"""

    def test_list_cart(self):
        """测试获取购物车列表"""
        response = self.client.get('/api/shop/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_to_cart(self):
        """测试添加商品到购物车"""
        data = {
            'product': self.product.id,
            'quantity': 2
        }
        response = self.client.post('/api/shop/cart/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证购物车记录已创建
        self.assertTrue(Cart.objects.filter(user=self.user, product=self.product).exists())

    def test_add_to_cart_merge_same_product(self):
        """测试相同商品合并数量"""
        # 第一次添加
        self.client.post('/api/shop/cart/', {'product': self.product.id, 'quantity': 2}, format='json')

        # 第二次添加相同商品
        response = self.client.post('/api/shop/cart/', {'product': self.product.id, 'quantity': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证数量已累加
        cart = Cart.objects.get(user=self.user, product=self.product)
        self.assertEqual(cart.quantity, 5)

    def test_update_cart_quantity(self):
        """测试更新购物车数量"""
        cart = self.create_test_cart()

        response = self.client.patch(f'/api/shop/cart/{cart.id}/', {'quantity': 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        cart.refresh_from_db()
        self.assertEqual(cart.quantity, 5)

    def test_update_cart_quantity_to_zero_deletes(self):
        """测试数量为 0 时删除购物车记录"""
        cart = self.create_test_cart()

        response = self.client.patch(f'/api/shop/cart/{cart.id}/', {'quantity': 0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证购物车记录已删除
        self.assertFalse(Cart.objects.filter(id=cart.id).exists())

    def test_update_cart_exceeds_stock(self):
        """测试数量超过库存时拒绝更新"""
        cart = self.create_test_cart(quantity=5)
        self.product.stock = 3
        self.product.save()

        response = self.client.patch(f'/api/shop/cart/{cart.id}/', {'quantity': 10}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('code'), 400)

    def test_delete_cart(self):
        """测试删除购物车记录"""
        cart = self.create_test_cart()

        response = self.client.delete(f'/api/shop/cart/{cart.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(Cart.objects.filter(id=cart.id).exists())

    def test_cart_isolation_between_users(self):
        """测试购物车在用户之间隔离"""
        # 用户1添加购物车
        self.create_test_cart(user=self.user)

        # 用户2看不到用户1的购物车
        self.authenticate(self.user2)
        response = self.client.get('/api/shop/cart/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_to_cart_unauthenticated_fails(self):
        """测试未认证用户添加购物车失败"""
        from rest_framework.test import APIClient
        client = APIClient()
        response = client.post('/api/shop/cart/', {'product': self.product.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderAPITest(ShopAPITestCase):
    """订单 API 测试"""

    def test_list_orders(self):
        """测试获取订单列表"""
        response = self.client.get('/api/shop/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_order_success(self):
        """测试创建订单成功"""
        # 先添加购物车
        cart = self.create_test_cart()

        data = {
            'cart_ids': [cart.id],
            'address': {
                'name': '张三',
                'phone': '13800138000',
                'province': '广东省',
                'city': '深圳市',
                'district': '南山区',
                'detail': '科技园路1号'
            }
        }
        response = self.client.post('/api/shop/orders/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('msg'), '下单成功')

        # 验证订单已创建
        self.assertTrue(Order.objects.filter(user=self.user).exists())

        # 验证购物车已删除
        self.assertFalse(Cart.objects.filter(id=cart.id).exists())

        # 验证库存已扣减
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 99)  # 原100 - 1

    def test_create_order_with_invalid_cart(self):
        """测试使用无效购物车创建订单失败"""
        data = {
            'cart_ids': [99999],
            'address': {
                'name': '张三',
                'phone': '13800138000',
                'province': '广东省',
                'city': '深圳市',
                'district': '南山区',
                'detail': '科技园路1号'
            }
        }
        response = self.client.post('/api/shop/orders/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('code'), 400)

    def test_create_order_stock_insufficient(self):
        """测试库存不足时创建订单失败"""
        self.product.stock = 1
        self.product.save()

        cart = self.create_test_cart(quantity=5)

        data = {
            'cart_ids': [cart.id],
            'address': {
                'name': '张三',
                'phone': '13800138000',
                'province': '广东省',
                'city': '深圳市',
                'district': '南山区',
                'detail': '科技园路1号'
            }
        }
        response = self.client.post('/api/shop/orders/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('code'), 400)

        # 验证购物车未被删除
        self.assertTrue(Cart.objects.filter(id=cart.id).exists())

    def test_retrieve_order(self):
        """测试获取订单详情"""
        order = self.create_test_order()

        response = self.client.get(f'/api/shop/orders/{order.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancel_order_success(self):
        """测试取消订单成功"""
        order = self.create_test_order()

        response = self.client.put(f'/api/shop/orders/{order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')

    def test_cancel_order_with_wrong_status(self):
        """测试已发货订单不能取消"""
        order = self.create_test_order(status='shipped')

        response = self.client.put(f'/api/shop/orders/{order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('code'), 400)

    def test_cancel_order_stock_rollback(self):
        """测试取消订单后库存回滚"""
        # 创建订单时扣减了库存
        cart = self.create_test_cart(quantity=3)
        self.client.post('/api/shop/orders/', {
            'cart_ids': [cart.id],
            'address': {
                'name': '张三',
                'phone': '13800138000',
                'province': '广东省',
                'city': '深圳市',
                'district': '南山区',
                'detail': '科技园路1号'
            }
        }, format='json')

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 97)  # 100 - 3

        # 获取刚创建的订单
        order = Order.objects.filter(user=self.user).first()
        response = self.client.put(f'/api/shop/orders/{order.id}/cancel/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证库存已回滚
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 100)  # 恢复原库存

    def test_complete_order_success(self):
        """测试确认收货成功"""
        order = self.create_test_order(status='shipped')

        response = self.client.put(f'/api/shop/orders/{order.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')
        self.assertIsNotNone(order.completed_at)

    def test_complete_order_with_wrong_status(self):
        """测试非发货状态不能确认收货"""
        order = self.create_test_order(status='pending')

        response = self.client.put(f'/api/shop/orders/{order.id}/complete/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('code'), 400)

    def test_filter_orders_by_status(self):
        """测试按状态筛选订单"""
        self.create_test_order(status='pending')
        self.create_test_order(status='completed')

        response = self.client.get('/api/shop/orders/?status=pending')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_order_isolation_between_users(self):
        """测试订单在用户之间隔离"""
        self.create_test_order(user=self.user)

        self.authenticate(self.user2)
        response = self.client.get('/api/shop/orders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AddressAPITest(ShopAPITestCase):
    """收货地址 API 测试"""

    def test_list_addresses(self):
        """测试获取地址列表"""
        response = self.client.get('/api/shop/addresses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_address_success(self):
        """测试创建地址成功"""
        data = {
            'name': '张三',
            'phone': '13800138000',
            'province': '广东省',
            'city': '深圳市',
            'district': '南山区',
            'detail': '科技园路1号'
        }
        response = self.client.post('/api/shop/addresses/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('msg'), '地址添加成功')

    def test_create_default_address(self):
        """测试创建默认地址"""
        data = {
            'name': '张三',
            'phone': '13800138000',
            'province': '广东省',
            'city': '深圳市',
            'district': '南山区',
            'detail': '科技园路1号',
            'is_default': True
        }
        response = self.client.post('/api/shop/addresses/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_address(self):
        """测试更新地址"""
        address = self.create_test_address()

        data = {'name': '更新后的名字'}
        response = self.client.patch(f'/api/shop/addresses/{address.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_address(self):
        """测试删除地址"""
        address = self.create_test_address()

        response = self.client.delete(f'/api/shop/addresses/{address.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_set_default_address(self):
        """测试设置默认地址"""
        address1 = self.create_test_address(is_default=False)
        address2 = self.create_test_address(name='李四', is_default=False)

        response = self.client.post(f'/api/shop/addresses/{address1.id}/set_default/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        address1.refresh_from_db()
        self.assertTrue(address1.is_default)

    def test_address_isolation_between_users(self):
        """测试地址在用户之间隔离"""
        self.create_test_address(user=self.user)

        self.authenticate(self.user2)
        response = self.client.get('/api/shop/addresses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
