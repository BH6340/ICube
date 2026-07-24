# -*- coding: utf-8 -*-
"""
商城模块序列化器

定义商品、分类、购物车、订单的数据序列化和验证逻辑，包括：
    - ProductCategorySerializer: 分类树形结构序列化
    - ProductListSerializer: 商品列表轻量序列化
    - ProductDetailSerializer: 商品详情完整序列化
    - CartSerializer: 购物车序列化（含商品信息）
    - CartCreateSerializer: 购物车创建验证
    - OrderSerializer: 订单序列化（含明细）
    - OrderCreateSerializer: 订单创建验证

设计特点：
    - **双重序列化器策略**：列表页轻量、详情页完整，减少数据传输
    - **嵌套序列化**：订单包含订单明细，分类包含子分类
    - **自定义验证**：购物车创建时验证商品上架状态和库存
"""

from rest_framework import serializers
from .models import ProductCategory, Product, Cart, Order, OrderItem, Address


class ProductCategorySerializer(serializers.ModelSerializer):
    """
    商品分类序列化器

    支持树形结构递归序列化，子分类通过 SerializerMethodField 获取。

    设计要点：
        - **递归序列化**：children 字段通过 get_children 方法递归序列化子分类
        - **完整字段**：包含分类的所有属性
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'parent', 'icon', 'sort_order', 'description', 'children']

    def get_children(self, obj):
        """递归获取并序列化子分类"""
        children = obj.children.all()
        return ProductCategorySerializer(children, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    """
    商品列表序列化器（轻量）

    用于商品列表页，只返回关键信息，减少数据传输量。

    设计要点：
        - **轻量字段**：不含完整描述等大字段
        - **分类名称**：通过 source 指定获取分类名称
    """
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'original_price', 'stock', 'images', 'thumbnail',
                  'is_on_sale', 'sales_count', 'category', 'category_name', 'specs', 'created_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    商品详情序列化器（完整）

    用于商品详情页，返回完整的商品信息。

    设计要点：
        - **完整字段**：包含 description 和 updated_at 等详情字段
        - **分类名称**：通过 source 指定获取分类名称
    """
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'original_price', 'stock', 'images',
                  'thumbnail', 'is_on_sale', 'sales_count', 'category', 'category_name', 'specs',
                  'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    """
    购物车序列化器

    包含商品详细信息，便于前端展示购物车列表。

    设计要点：
        - **商品信息**：通过 product_info SerializerMethodField 聚合商品详情
        - **规格展示**：selected_spec 直接返回 JSON 格式的规格信息
    """
    product_info = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'product', 'product_info', 'quantity', 'selected_spec', 'created_at']

    def get_product_info(self, obj):
        """聚合商品详情信息"""
        product = obj.product
        return {
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'thumbnail': product.thumbnail.url if product.thumbnail else None,
            'stock': product.stock,
            'specs': product.specs
        }


class CartCreateSerializer(serializers.ModelSerializer):
    """
    购物车创建序列化器

    包含商品上架状态和库存的验证逻辑。

    设计要点：
        - **验证逻辑**：validate 方法验证商品是否上架、库存是否充足
        - **简化字段**：只包含 product、quantity、selected_spec 三个字段
    """
    class Meta:
        model = Cart
        fields = ['product', 'quantity', 'selected_spec']

    def validate(self, attrs):
        """验证商品上架状态和库存"""
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)
        if not product.is_on_sale:
            raise serializers.ValidationError('商品已下架')
        if quantity > product.stock:
            raise serializers.ValidationError('库存不足')
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    """
    订单明细序列化器

    序列化订单中的每个商品项，包含商品名称和图片。

    设计要点：
        - **商品信息**：通过 source 获取商品名称，通过 SerializerMethodField 获取图片
        - **快照数据**：price 和 selected_spec 是下单时的快照，不受后续变动影响
    """
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'price', 'quantity', 'selected_spec']

    def get_product_image(self, obj):
        """获取商品缩略图 URL"""
        if obj.product.thumbnail:
            return obj.product.thumbnail.url
        return None


class OrderSerializer(serializers.ModelSerializer):
    """
    订单序列化器

    包含订单明细，返回完整的订单信息。

    设计要点：
        - **嵌套序列化**：items 字段使用 OrderItemSerializer 序列化订单明细
        - **完整字段**：包含所有状态时间戳和地址信息
    """
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'total_amount', 'status', 'address', 'items',
                  'created_at', 'paid_at', 'shipped_at', 'completed_at']


class OrderCreateSerializer(serializers.Serializer):
    """
    订单创建序列化器

    验证购物车 ID 和收货地址，不基于模型定义。

    设计要点：
        - **自定义字段**：cart_ids（购物车 ID 列表）和 address（收货地址字典）
        - **权限验证**：validate_cart_ids 验证购物车商品属于当前用户
    """
    cart_ids = serializers.ListField(child=serializers.IntegerField())
    address = serializers.DictField()

    def validate_cart_ids(self, cart_ids):
        """验证购物车商品存在且属于当前用户"""
        user = self.context['request'].user
        carts = Cart.objects.filter(id__in=cart_ids, user=user)
        if not carts.exists():
            raise serializers.ValidationError('购物车商品不存在')
        return cart_ids


class AddressSerializer(serializers.ModelSerializer):
    """
    收货地址序列化器

    序列化收货地址信息，包含完整地址和默认状态。

    设计要点：
        - **完整字段**：包含省市区和详细地址的所有字段
        - **默认标识**：is_default 字段标识默认地址
        - **只读字段**：full_address 通过 property 方法生成完整地址字符串
    """
    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = Address
        fields = ['id', 'name', 'phone', 'province', 'city', 'district', 'detail',
                  'is_default', 'sort_order', 'full_address', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']