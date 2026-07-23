# -*- coding: utf-8 -*-
"""
商城模块数据模型

定义商品、分类、购物车、订单的核心数据结构，包括：
    - ProductCategory: 商品分类（树形结构）
    - Product: 商品信息（含规格、库存、图片）
    - Cart: 购物车记录（用户+商品+规格）
    - Order: 订单信息（状态流转、地址）
    - OrderItem: 订单明细（订单与商品的关联）

设计特点：
    - **分类树形结构**：自关联实现多级分类
    - **商品规格 JSONField**：灵活存储不同商品的规格配置
    - **订单状态枚举**：STATUS_CHOICES 定义完整状态流转
    - **订单号生成**：时间戳 + UUID 保证唯一性
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class ProductCategory(models.Model):
    """
    商品分类模型

    使用自关联实现多级分类结构，支持无限层级。

    设计要点：
        - **树形结构**：parent 字段指向自身，实现分类层级
        - **排序支持**：sort_order 控制分类显示顺序
        - **图标字段**：icon 用于前端展示分类图标
        - **级联删除**：子分类的 parent 设为 NULL（SET_NULL），而非级联删除
    """
    name = models.CharField('分类名称', max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children'
    )
    icon = models.CharField('图标', max_length=100, blank=True)
    sort_order = models.IntegerField('排序', default=0)
    description = models.TextField('描述', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'shop'
        db_table = 'shop_product_category'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    商品模型

    定义商品的核心属性，包括价格、库存、规格、图片等。

    设计要点：
        - **价格体系**：price（售价）+ original_price（原价），支持折扣展示
        - **库存管理**：stock 字段配合 F 表达式实现并发安全的库存扣减
        - **规格存储**：specs 使用 JSONField 灵活存储不同商品的规格配置
        - **图片管理**：images（多图）+ thumbnail（缩略图）双字段设计
        - **上下架控制**：is_on_sale 控制商品是否可购买
    """
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True
    )
    name = models.CharField('商品名称', max_length=200)
    description = models.TextField('描述', blank=True)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        '原价', max_digits=10, decimal_places=2, null=True, blank=True
    )
    stock = models.IntegerField('库存', default=0)
    images = models.JSONField('商品图片', default=list)
    thumbnail = models.ImageField(
        '缩略图', upload_to='products/', null=True, blank=True
    )
    is_on_sale = models.BooleanField('是否上架', default=True)
    sales_count = models.IntegerField('销量', default=0)
    specs = models.JSONField('规格', default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'shop'
        db_table = 'shop_product'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Cart(models.Model):
    """
    购物车模型

    记录用户添加到购物车的商品信息，支持规格选择。

    设计要点：
        - **规格记录**：selected_spec 使用 JSONField 记录用户选择的规格
        - **数量控制**：quantity 默认值为 1，支持累加
        - **唯一性约束**：用户+商品+规格组合唯一（业务层保证）
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='carts')
    quantity = models.IntegerField('数量', default=1)
    selected_spec = models.JSONField('选中规格', default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'shop'
        db_table = 'shop_cart'

    def __str__(self):
        return f'{self.user.username} - {self.product.name}'


class Order(models.Model):
    """
    订单模型

    定义订单的核心信息，包括状态流转、金额、地址等。

    订单状态流转：
        pending（待付款）→ paid（已付款）→ shipped（已发货）→ completed（已完成）
                          ↘ cancelled（已取消）
                          ↗ cancelled（已取消）← paid

    设计要点：
        - **状态枚举**：STATUS_CHOICES 定义完整的订单状态
        - **时间戳记录**：paid_at、shipped_at、completed_at 记录各阶段时间
        - **地址存储**：address 使用 JSONField 灵活存储收货地址
        - **订单号生成**：generate_order_no 类方法生成唯一订单号
    """
    STATUS_CHOICES = [
        ('pending', '待付款'),
        ('paid', '已付款'),
        ('shipped', '已发货'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_no = models.CharField('订单号', max_length=32, unique=True)
    total_amount = models.DecimalField('总金额', max_digits=12, decimal_places=2)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.JSONField('收货地址')
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField('付款时间', null=True, blank=True)
    shipped_at = models.DateTimeField('发货时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        app_label = 'shop'
        db_table = 'shop_order'
        ordering = ['-created_at']

    def __str__(self):
        return self.order_no

    @classmethod
    def generate_order_no(cls):
        """
        生成唯一订单号

        订单号格式：ORD + 时间戳(14位) + UUID前8位(大写)
        示例：ORD20240101120000ABC12345

        设计要点：
            - **时间戳**：精确到秒，便于排序和查询
            - **UUID**：保证唯一性，防止并发冲突
            - **前缀标识**：ORD 便于区分订单类型
        """
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = str(uuid.uuid4())[:8].upper()
        return f'ORD{timestamp}{random_str}'


class OrderItem(models.Model):
    """
    订单明细模型

    分解订单与商品的多对多关系，记录每个商品的购买信息。

    设计要点：
        - **快照存储**：price 字段记录下单时的价格，不受后续价格变动影响
        - **规格记录**：selected_spec 记录购买时选择的规格
        - **关联查询**：通过 items 反向关联查询订单的所有商品
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField('单价', max_digits=10, decimal_places=2)
    quantity = models.IntegerField('数量')
    selected_spec = models.JSONField('选中规格', default=dict)

    class Meta:
        app_label = 'shop'
        db_table = 'shop_order_item'

    def __str__(self):
        return f'{self.order.order_no} - {self.product.name}'