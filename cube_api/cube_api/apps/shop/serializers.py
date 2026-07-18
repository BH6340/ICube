from rest_framework import serializers
from .models import ProductCategory, Product, Cart, Order, OrderItem


class ProductCategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'parent', 'icon', 'sort_order', 'description', 'children']

    def get_children(self, obj):
        children = obj.children.all()
        return ProductCategorySerializer(children, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'original_price', 'stock', 'images', 'thumbnail',
                  'is_on_sale', 'sales_count', 'category', 'category_name', 'specs', 'created_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'original_price', 'stock', 'images',
                  'thumbnail', 'is_on_sale', 'sales_count', 'category', 'category_name', 'specs',
                  'created_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    product_info = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'product', 'product_info', 'quantity', 'selected_spec', 'created_at']

    def get_product_info(self, obj):
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
    class Meta:
        model = Cart
        fields = ['product', 'quantity', 'selected_spec']

    def validate(self, attrs):
        product = attrs.get('product')
        quantity = attrs.get('quantity', 1)
        if not product.is_on_sale:
            raise serializers.ValidationError('商品已下架')
        if quantity > product.stock:
            raise serializers.ValidationError('库存不足')
        return attrs


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'price', 'quantity', 'selected_spec']

    def get_product_image(self, obj):
        if obj.product.thumbnail:
            return obj.product.thumbnail.url
        return None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'total_amount', 'status', 'address', 'items',
                  'created_at', 'paid_at', 'shipped_at', 'completed_at']


class OrderCreateSerializer(serializers.Serializer):
    cart_ids = serializers.ListField(child=serializers.IntegerField())
    address = serializers.DictField()

    def validate_cart_ids(self, cart_ids):
        user = self.context['request'].user
        carts = Cart.objects.filter(id__in=cart_ids, user=user)
        if not carts.exists():
            raise serializers.ValidationError('购物车商品不存在')
        return cart_ids