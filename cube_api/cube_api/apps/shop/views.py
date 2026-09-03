# -*- coding: utf-8 -*-
"""
商城模块视图集

该模块处理商品、购物车、订单的完整业务逻辑，包括：
    - 商品分类与搜索
    - 购物车增删改查
    - 订单创建与状态流转
    - 支付宝支付集成
    - 库存管理与并发控制

设计特点：
    - **事务原子性**：订单创建、库存扣减、购物车删除使用 @transaction.atomic 保证一致性
    - **库存并发控制**：使用 F 表达式避免并发超卖问题
    - **订单状态流转**：pending → paid → shipped → completed / cancelled
    - **幂等性保证**：支付宝回调使用 select_for_update 防止重复处理
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import ProductCategory, Product, Cart, Order, OrderItem, Address
from .serializers import (
    ProductCategorySerializer, ProductListSerializer, ProductDetailSerializer,
    CartSerializer, CartCreateSerializer, OrderSerializer, OrderCreateSerializer,
    AddressSerializer
)
from .alipay_config import ALIPAY_CONFIG, generate_alipay_qr_code, generate_alipay_url, verify_alipay_notify
from decimal import Decimal
from utils.common_response import APIResponse
from loguru import logger


class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    商品分类视图集

    提供商品分类的树形结构查询，仅支持只读操作。

    设计要点：
        - **树形结构查询**：只查询顶级分类（parent__isnull=True），子分类通过 SerializerMethodField 递归获取
        - **无分页**：分类数据量较小，直接返回全部
    """
    queryset = ProductCategory.objects.filter(parent__isnull=True)
    serializer_class = ProductCategorySerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    商品视图集

    提供商品列表和详情查询，支持分类过滤、价格区间、关键词搜索和排序。

    设计要点：
        - **双重序列化器**：列表页使用轻量的 ProductListSerializer，详情页使用完整的 ProductDetailSerializer
        - **分类递归查询**：查询子分类商品时，同时包含父分类和子分类的商品
        - **多条件过滤**：支持分类、价格区间、关键词搜索和排序
    """
    queryset = Product.objects.filter(is_on_sale=True)
    serializer_class = ProductListSerializer

    def get_queryset(self):
        """
        获取商品查询集，支持多条件过滤

        过滤参数：
            - category: 分类 ID（包含子分类）
            - price_min: 最低价格
            - price_max: 最高价格
            - keyword: 商品名称关键词
            - sort: 排序字段（默认 -created_at）
        """
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            category_ids = list(ProductCategory.objects.filter(id=category).values_list('id', flat=True))
            children_ids = list(ProductCategory.objects.filter(parent_id=category).values_list('id', flat=True))
            queryset = queryset.filter(category_id__in=category_ids + children_ids)

        price_min = self.request.query_params.get('price_min')
        price_max = self.request.query_params.get('price_max')
        if price_min:
            queryset = queryset.filter(price__gte=price_min)
        if price_max:
            queryset = queryset.filter(price__lte=price_max)

        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(name__icontains=keyword)

        sort = self.request.query_params.get('sort', '-created_at')
        queryset = queryset.order_by(sort)

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """获取商品详情，使用完整序列化器"""
        instance = self.get_object()
        serializer = ProductDetailSerializer(instance)
        return APIResponse(data=serializer.data)


class CartViewSet(viewsets.ModelViewSet):
    """
    购物车视图集

    处理用户购物车的增删改查操作，仅登录用户可访问。

    设计要点：
        - **购物车合并逻辑**：相同商品相同规格合并数量，使用 F 表达式原子更新
        - **权限控制**：用户只能访问自己的购物车
        - **数量边界处理**：数量 <= 0 时自动删除，数量 > 库存时拒绝更新
    """
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """过滤当前用户的购物车"""
        return super().get_queryset().filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        添加商品到购物车

        合并逻辑：
            1. 如果购物车已存在相同商品且规格相同，数量累加（使用 F 表达式）
            2. 如果不存在或规格不同，创建新的购物车记录
        """
        serializer = CartCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        product = serializer.validated_data['product']
        quantity = serializer.validated_data.get('quantity', 1)
        selected_spec = serializer.validated_data.get('selected_spec', {})

        cart = Cart.objects.filter(
            user=request.user,
            product=product
        ).first()

        if cart and cart.selected_spec == selected_spec:
            cart.quantity = F('quantity') + quantity
            cart.save()
            cart.refresh_from_db()
        else:
            cart = Cart.objects.create(
                user=request.user,
                product=product,
                quantity=quantity,
                selected_spec=selected_spec
            )

        return APIResponse(data=CartSerializer(cart).data, msg='添加成功')

    def update(self, request, *args, **kwargs):
        """
        更新购物车数量

        特殊处理：
            - 数量 <= 0：删除购物车记录
            - 数量 > 库存：拒绝更新，返回错误
        """
        instance = self.get_object()
        quantity = request.data.get('quantity')
        if quantity is not None:
            if quantity <= 0:
                instance.delete()
                return APIResponse(msg='已删除')
            if quantity > instance.product.stock:
                return APIResponse(code=400, msg='库存不足')
            instance.quantity = quantity
            instance.save()
        return APIResponse(data=CartSerializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        """删除购物车记录"""
        instance = self.get_object()
        instance.delete()
        return APIResponse(msg='删除成功')


class OrderViewSet(viewsets.ModelViewSet):
    """
    订单视图集

    处理订单的完整生命周期，包括创建、支付、取消、完成和支付宝回调。

    订单状态流转：
        pending（待付款）→ paid（已付款）→ shipped（已发货）→ completed（已完成）
                          ↘ cancelled（已取消）
                          ↗ cancelled（已取消）← paid

    自定义动作：
        - pay: 获取支付链接
        - cancel: 取消订单（库存回滚）
        - complete: 确认收货
        - alipay_notify: 支付宝异步回调（无需认证）
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """过滤当前用户的订单，支持状态筛选"""
        queryset = super().get_queryset().filter(user=self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        """
        获取订单详情

        支持两种查询方式：
            1. 通过订单号查询（优先）
            2. 通过 ID 查询（兼容）
        """
        pk = kwargs.get('pk')
        try:
            order = Order.objects.get(order_no=pk, user=request.user)
        except Order.DoesNotExist:
            try:
                order = self.get_object()
            except Exception:
                return APIResponse(code=404, msg='订单不存在')
        serializer = OrderSerializer(order)
        return APIResponse(data=serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        创建订单（核心业务逻辑）

        事务流程：
            1. 验证购物车商品存在且属于当前用户
            2. 遍历购物车，检查库存是否充足
            3. 使用 F 表达式扣减库存、增加销量（原子操作）
            4. 删除购物车记录
            5. 生成订单号并创建订单
            6. 创建订单明细（OrderItem）

        设计要点：
            - **事务原子性**：使用 @transaction.atomic 确保所有操作要么全部成功，要么全部回滚
            - **库存并发控制**：使用 F('stock') - quantity 避免并发超卖
            - **订单号生成**：时间戳 + UUID 保证唯一性
        """
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        cart_ids = serializer.validated_data['cart_ids']
        address = serializer.validated_data['address']

        carts = Cart.objects.filter(id__in=cart_ids, user=request.user)
        if not carts.exists():
            return APIResponse(code=400, msg='购物车商品不存在')

        total_amount = 0
        order_items = []

        for cart in carts:
            if cart.quantity > cart.product.stock:
                return APIResponse(code=400, msg=f'{cart.product.name}库存不足')

            item_total = cart.product.price * cart.quantity
            total_amount += item_total

            order_items.append({
                'product': cart.product,
                'price': cart.product.price,
                'quantity': cart.quantity,
                'selected_spec': cart.selected_spec
            })

            cart.product.stock = F('stock') - cart.quantity
            cart.product.sales_count = F('sales_count') + cart.quantity
            cart.product.save()

        carts.delete()

        order = Order.objects.create(
            user=request.user,
            order_no=Order.generate_order_no(),
            total_amount=total_amount,
            address=address
        )

        for item_data in order_items:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                price=item_data['price'],
                quantity=item_data['quantity'],
                selected_spec=item_data['selected_spec']
            )

        return APIResponse(data=OrderSerializer(order).data, msg='下单成功')

    def pay(self, request, pk=None):
        """
        获取支付宝支付链接

        仅待付款状态的订单可发起支付，生成网页支付 URL 返回给前端。

        异常处理：
            - 订单状态不正确：返回错误
            - 支付宝配置失败：记录日志并返回服务不可用
        """
        order = self.get_object()
        if order.status != 'pending':
            return APIResponse(code=400, msg='订单状态不正确')

        subject = f'魔方商城订单-{order.order_no}'

        pay_url = generate_alipay_url(order.order_no, order.total_amount, subject)
        if pay_url:
            return APIResponse(data={
                'order': OrderSerializer(order).data,
                'pay_url': pay_url,
            }, msg='获取支付链接成功')

        logger.warning(f"支付宝支付失败 - 订单 {order.order_no}: SDK 初始化异常, return_url 或 notify_url 不可用")
        return APIResponse(code=503, msg='支付宝支付接口配置异常，请稍后重试')

    @transaction.atomic
    def cancel(self, request, pk=None):
        """
        取消订单

        仅待付款和已付款状态的订单可取消，取消后库存回滚。

        回滚逻辑：
            1. 将订单状态改为 cancelled
            2. 使用 F 表达式恢复库存、减少销量
        """
        order = self.get_object()
        if order.status not in ['pending', 'paid']:
            return APIResponse(code=400, msg='订单状态不允许取消')

        order.status = 'cancelled'
        order.save()

        for item in order.items.all():
            item.product.stock = F('stock') + item.quantity
            item.product.sales_count = F('sales_count') - item.quantity
            item.product.save()

        return APIResponse(data=OrderSerializer(order).data, msg='取消成功')

    @transaction.atomic
    def complete(self, request, pk=None):
        """
        确认收货

        仅已发货状态的订单可确认收货，确认后订单状态改为 completed。
        """
        order = self.get_object()
        if order.status != 'shipped':
            return APIResponse(code=400, msg='订单状态不正确')

        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()

        return APIResponse(data=OrderSerializer(order).data, msg='确认收货成功')

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='notify')
    @transaction.atomic
    def alipay_notify(self, request):
        """
        支付宝异步回调接口

        无需登录认证，支付宝服务器直接调用此接口通知支付结果。

        处理流程：
            1. 解析回调数据（DRF QueryDict 转换）
            2. 验证签名（双重验签：SDK + 手动 RSA2）
            3. 查询订单并加锁（select_for_update 防止并发处理）
            4. 根据 trade_status 更新订单状态
            5. 返回 'success' 或 'fail'

        幂等性保证：
            - 使用 select_for_update 锁定订单记录
            - 仅在订单状态为 pending 时更新为 paid
            - 返回 'success' 表示已处理，支付宝不再重试
        """
        raw_body = request.body  # 先于 request.data 读取，否则流被消耗
        raw_data = {k: v[0] if isinstance(v, list) else v for k, v in request.data.items()}
        logger.info(f"支付宝回调原始数据: {raw_data}")

        try:
            verified = verify_alipay_notify(request.data, raw_body)
        except Exception as e:
            logger.error(f"支付宝回调签名验证异常: {e}")
            return Response('fail')

        if not verified:
            logger.warning(f"支付宝回调签名验证失败: {raw_data.get('out_trade_no', 'unknown')}")
            return Response('fail')

        order_no = raw_data.get('out_trade_no')
        trade_status = raw_data.get('trade_status')
        logger.info(f"支付宝回调验证通过 - 订单 {order_no}, 状态 {trade_status}")

        # 安全校验：app_id 必须一致
        callback_app_id = raw_data.get('app_id', '')
        if callback_app_id and callback_app_id != ALIPAY_CONFIG['app_id']:
            logger.warning(f"支付宝回调 app_id 不匹配: 回调={callback_app_id}, 配置={ALIPAY_CONFIG['app_id']}")
            return Response('fail')

        try:
            order = Order.objects.select_for_update().get(order_no=order_no)
            # 安全校验：金额必须一致
            callback_amount = Decimal(raw_data.get('total_amount', '0'))
            if callback_amount != order.total_amount:
                logger.warning(f"支付宝回调金额不匹配: 回调={callback_amount}, 订单={order.total_amount}, 订单号={order_no}")
                return Response('fail')
            if trade_status in ('TRADE_SUCCESS', 'TRADE_FINISHED'):
                if order.status == 'pending':
                    order.status = 'paid'
                    order.paid_at = timezone.now()
                    order.save()
                    logger.info(f"订单 {order_no} 已标记为已支付")
                else:
                    logger.info(f"订单 {order_no} 已处理(status={order.status}), 跳过重复回调")
            return Response('success')
        except Order.DoesNotExist:
            logger.error(f"支付宝回调 - 订单 {order_no} 不存在")
            return Response('fail')


class AddressViewSet(viewsets.ModelViewSet):
    """
    收货地址视图集

    处理用户收货地址的完整生命周期，包括增删改查和默认地址设置。

    设计要点：
        - **权限控制**：用户只能访问和管理自己的地址
        - **默认地址唯一性**：同一用户只能有一个默认地址，创建或设置默认时自动取消其他默认地址
        - **排序管理**：按 sort_order 排序，默认地址排在最前面
        - **删除处理**：删除默认地址时，自动将第一个地址设为默认
    """
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """过滤当前用户的地址列表"""
        return super().get_queryset().filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        获取当前用户的地址列表

        返回结果按 is_default（默认地址优先）和 sort_order 排序。
        """
        queryset = self.get_queryset().order_by('-is_default', 'sort_order')
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)

    def create(self, request, *args, **kwargs):
        """
        创建新地址

        如果设置了 is_default=True，自动将用户的其他默认地址取消。
        如果用户没有默认地址，新创建的地址自动设为默认。
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        is_default = serializer.validated_data.get('is_default', False)
        user = request.user

        if is_default:
            Address.objects.filter(user=user, is_default=True).update(is_default=False)
        else:
            if not Address.objects.filter(user=user, is_default=True).exists():
                serializer.validated_data['is_default'] = True

        serializer.save(user=user)
        return APIResponse(data=serializer.data, msg='地址添加成功')

    def update(self, request, *args, **kwargs):
        """
        更新地址

        如果设置了 is_default=True，自动将用户的其他默认地址取消。
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        is_default = serializer.validated_data.get('is_default', False)
        if is_default and not instance.is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        serializer.save()
        return APIResponse(data=serializer.data, msg='地址更新成功')

    def partial_update(self, request, *args, **kwargs):
        """部分更新地址（PATCH）"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        删除地址

        如果删除的是默认地址，自动将用户的第一个地址设为默认。
        """
        instance = self.get_object()
        is_default_deleted = instance.is_default
        instance.delete()

        if is_default_deleted:
            first_address = Address.objects.filter(user=request.user).first()
            if first_address:
                first_address.is_default = True
                first_address.save()

        return APIResponse(msg='地址删除成功')

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        设置默认地址

        将指定地址设为默认地址，同时取消其他地址的默认状态。
        """
        address = self.get_object()
        if address.is_default:
            return APIResponse(msg='该地址已经是默认地址')

        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save()

        return APIResponse(data=AddressSerializer(address).data, msg='默认地址设置成功')