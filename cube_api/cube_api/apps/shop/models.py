from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class ProductCategory(models.Model):
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
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_str = str(uuid.uuid4())[:8].upper()
        return f'ORD{timestamp}{random_str}'


class OrderItem(models.Model):
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