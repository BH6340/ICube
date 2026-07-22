from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import ProductCategory, Product, Cart, Order, OrderItem
from .serializers import (
    ProductCategorySerializer, ProductListSerializer, ProductDetailSerializer,
    CartSerializer, CartCreateSerializer, OrderSerializer, OrderCreateSerializer
)
from .alipay_config import generate_alipay_qr_code, generate_alipay_url, verify_alipay_notify
from utils.common_response import APIResponse
from loguru import logger


class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductCategory.objects.filter(parent__isnull=True)
    serializer_class = ProductCategorySerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(data=serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_on_sale=True)
    serializer_class = ProductListSerializer

    def get_queryset(self):
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
        instance = self.get_object()
        serializer = ProductDetailSerializer(instance)
        return APIResponse(data=serializer.data)


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
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
        instance = self.get_object()
        instance.delete()
        return APIResponse(msg='删除成功')


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        return queryset

    def retrieve(self, request, *args, **kwargs):
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
        order = self.get_object()
        if order.status != 'pending':
            return APIResponse(code=400, msg='订单状态不正确')

        subject = f'魔方商城订单-{order.order_no}'

        # 优先尝试网页支付（PC 端跳转）
        pay_url = generate_alipay_url(order.order_no, order.total_amount, subject)
        if pay_url:
            return APIResponse(data={
                'order': OrderSerializer(order).data,
                'pay_url': pay_url,
                'qr_code': None,
            }, msg='获取支付链接成功')

        # 降级：尝试生成扫码支付
        qr_code = generate_alipay_qr_code(order.order_no, order.total_amount, subject)
        if qr_code:
            return APIResponse(data={
                'order': OrderSerializer(order).data,
                'pay_url': None,
                'qr_code': qr_code,
            }, msg='获取支付二维码成功')

        # 支付宝配置失败
        logger.warning(f"支付宝支付失败 - 订单 {order.order_no}: SDK 初始化异常, return_url 或 notify_url 不可用")
        return APIResponse(code=503, msg='支付宝支付接口配置异常，请稍后重试')

    def cancel(self, request, pk=None):
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
        order = self.get_object()
        if order.status != 'shipped':
            return APIResponse(code=400, msg='订单状态不正确')

        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()

        return APIResponse(data=OrderSerializer(order).data, msg='确认收货成功')

    @action(detail=False, methods=['post'], permission_classes=[AllowAny], url_path='notify')
    def alipay_notify(self, request):
        """支付宝异步回调 - 无需登录认证"""
        data = request.data
        if not verify_alipay_notify(data):
            logger.warning(f"支付宝回调签名验证失败: {data.get('out_trade_no', 'unknown')}")
            return Response('fail')

        order_no = data.get('out_trade_no')
        trade_status = data.get('trade_status')
        logger.info(f"支付宝回调 - 订单 {order_no}, 状态 {trade_status}")

        try:
            order = Order.objects.select_for_update().get(order_no=order_no)
            if trade_status in ('TRADE_SUCCESS', 'TRADE_FINISHED'):
                if order.status == 'pending':
                    order.status = 'paid'
                    order.paid_at = timezone.now()
                    order.save()
                    logger.info(f"订单 {order_no} 已标记为已支付")
            return Response('success')
        except Order.DoesNotExist:
            logger.error(f"支付宝回调 - 订单 {order_no} 不存在")
            return Response('fail')