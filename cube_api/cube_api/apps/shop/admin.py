# -*- coding: utf-8 -*-
"""
商城模块后台管理

基于 django-unfold 的现代化后台管理配置，包括：
    - ProductCategoryAdmin: 商品分类管理（树形结构）
    - ProductAdmin: 商品管理（含缩略图预览、库存Badge、批量上下架）
    - CartAdmin: 购物车记录管理
    - OrderAdmin: 订单管理（含状态Badge、批量发货/完成）
    - OrderItemAdmin: 订单明细管理
"""

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils import timezone
from unfold.admin import ModelAdmin
from unfold.decorators import display, action

from .models import ProductCategory, Product, Cart, Order, OrderItem, Address


@admin.register(ProductCategory)
class ProductCategoryAdmin(ModelAdmin):
    """
    商品分类后台管理

    配置分类列表的展示、筛选、搜索与排序编辑，
    支持通过 parent 筛选查看子分类，sort_order 可在列表直接编辑。
    """

    # list_display: 列表页展示字段配置
    # 为什么这样配：展示分类核心信息，便于快速识别分类层级与排序
    list_display = ['name', 'parent', 'sort_order', 'created_at']

    # list_filter: 列表页侧边筛选器配置
    # 为什么这样配：通过 parent 筛选可快速查看某父分类下的所有子分类
    list_filter = ['parent']

    # search_fields: 搜索框可搜索字段配置
    # 为什么这样配：分类名称是识别分类的主要方式，按名称搜索最直观
    search_fields = ['name']

    # list_editable: 列表页可直接编辑字段配置
    # 为什么这样配：sort_order 需要频繁调整，列表内编辑避免逐条进入详情页
    list_editable = ['sort_order']


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    """
    商品后台管理

    重点管理类，提供：
        - 缩略图预览（@display）
        - 库存状态 Badge（@display，按库存量分色）
        - 上架状态 Badge（@display）
        - 批量上架/下架动作（@action）
        - 分组字段配置（fieldsets）
    """

    # list_display: 列表页展示字段配置
    # 为什么这样配：缩略图+名称+分类+价格+库存Badge+上架Badge+销量+创建时间
    # 一屏展示商品运营所需的关键信息，Badge 让状态一目了然
    list_display = [
        'thumbnail_preview',
        'images_preview',
        'name',
        'category',
        'price',
        'stock_badge',
        'is_on_sale_badge',
        'sales_count',
        'created_at',
    ]

    # search_fields: 搜索框可搜索字段配置
    # 为什么这样配：商品名称和描述都可能包含用户查找的关键词
    search_fields = ['name', 'description']

    # list_filter: 列表页侧边筛选器配置
    # 为什么这样配：按分类筛选便于品类管理，按上架状态筛选便于上下架核对，按创建时间筛选便于新商品排查
    list_filter = ['category', 'is_on_sale', 'created_at']

    # fieldsets: 详情页字段分组配置
    # 为什么这样配：商品字段较多，分组展示提升可读性与编辑效率
    fieldsets = (
        # 基础信息组：商品归属分类与基础描述信息
        ('基础信息', {
            'fields': ('category', 'name', 'description'),
        }),
        # 价格库存组：与销售策略直接相关的字段集中管理
        ('价格库存', {
            'fields': ('price', 'original_price', 'stock', 'is_on_sale', 'sales_count'),
        }),
        # 图片组：缩略图与多图分离，避免与文本字段混杂
        ('图片', {
            'fields': ('thumbnail', 'images'),
        }),
        # 规格组：规格配置独立分组，便于运营维护
        ('规格', {
            'fields': ('specs',),
        }),
    )

    # readonly_fields: 只读字段配置
    # 为什么这样配：sales_count 为系统统计字段，由订单流程自动更新，人工修改会导致数据失真
    readonly_fields = ['sales_count']

    # raw_id_fields: 外键弹窗选择字段配置
    # 为什么这样配：分类数量可能很多，下拉框会加载全部数据影响性能，改为弹窗搜索选择
    raw_id_fields = ['category']

    # actions: 自定义批量动作配置
    # 为什么这样配：批量上下架是日常运营高频操作，提供一键批量处理提升效率
    actions = ['batch_on_sale', 'batch_off_sale']

    @display(description="缩略图", ordering=None)
    def thumbnail_preview(self, obj):
        """
        缩略图预览：在列表页展示商品缩略图
        """
        if not obj.thumbnail:
            return '暂无图片'
        return mark_safe(
            f'<img src="{obj.thumbnail.url}" '
            f'style="max-width: 80px; max-height: 80px; object-fit: cover; '
            f'border-radius: 4px;" />'
        )

    @display(description="多图预览", ordering=None)
    def images_preview(self, obj):
        """
        多图预览：展示商品的额外图片（最多显示3张缩略图）

        images 字段是 JSONField，存储图片URL列表
        """
        if not obj.images or not isinstance(obj.images, list):
            return '无'
        preview_html = ''
        for idx, img_url in enumerate(obj.images[:3]):
            preview_html += f'<img src="{img_url}" style="max-width:40px;max-height:40px;object-fit:cover;border-radius:2px;margin-right:2px;" />'
        if len(obj.images) > 3:
            preview_html += f'<span style="font-size:12px;color:#999;">+{len(obj.images)-3}</span>'
        return mark_safe(preview_html)

    @display(description="库存", ordering="stock")
    def stock_badge(self, obj):
        """
        @display 装饰器作用：将方法注册为列表页可展示的列，ordering 指定按 stock 字段排序

        库存状态 Badge：按库存量分色展示，
            - 0 件：红色（缺货，需紧急补货）
            - 小于 10 件：黄色（库存偏低，需关注）
            - 大于等于 10 件：绿色（库存充足）
        使用 Tailwind CSS 类名渲染 Badge 样式。
        """
        if obj.stock == 0:
            # 缺货：红色 Badge
            color_class = 'bg-red-100 text-red-800'
            text = '缺货'
        elif obj.stock < 10:
            # 库存偏低：黄色 Badge
            color_class = 'bg-yellow-100 text-yellow-800'
            text = f'{obj.stock}件'
        else:
            # 库存充足：绿色 Badge
            color_class = 'bg-green-100 text-green-800'
            text = f'{obj.stock}件'
        # mark_safe 标记 HTML 安全，使用 Tailwind CSS 类名渲染 Badge
        return mark_safe(
            f'<span class="px-2 py-1 rounded-full text-xs font-medium {color_class}">{text}</span>'
        )

    @display(description="上架状态", boolean=True, ordering="is_on_sale")
    def is_on_sale_badge(self, obj):
        """
        @display 装饰器作用：将方法注册为列表页可展示的列，
        boolean=True 让 unfold 渲染为图标样式（对勾/叉），ordering 指定排序字段

        上架状态 Badge：直观展示商品上架/下架状态。
        """
        # 直接返回布尔值，由 unfold 的 boolean 模式渲染为图标
        return obj.is_on_sale

    @action(description="批量上架")
    def batch_on_sale(self, request, queryset):
        """
        @action 装饰器作用：将方法注册为批量动作，description 指定动作显示名称

        批量上架：将选中商品的 is_on_sale 设为 True，
        适用于新品批量上架或临时下架商品恢复销售的场景。
        """
        # update 批量更新，避免逐条 save 触发多次 SQL
        updated = queryset.update(is_on_sale=True)
        self.message_user(request, f'成功上架 {updated} 件商品')

    @action(description="批量下架")
    def batch_off_sale(self, request, queryset):
        """
        @action 装饰器作用：将方法注册为批量动作，description 指定动作显示名称

        批量下架：将选中商品的 is_on_sale 设为 False，
        适用于缺货、违规或季节性商品批量下架的场景。
        """
        # update 批量更新，避免逐条 save 触发多次 SQL
        updated = queryset.update(is_on_sale=False)
        self.message_user(request, f'成功下架 {updated} 件商品')


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    """
    购物车后台管理

    主要用于排查用户购物车异常（如数量错误、商品失效），
    配置 user 与 product 的弹窗选择以应对大数据量。
    """

    # list_display: 列表页展示字段配置
    # 为什么这样配：展示用户、商品、数量、加入时间，便于排查购物车记录问题
    list_display = ['user', 'product', 'quantity', 'created_at']

    # list_filter: 列表页侧边筛选器配置
    # 为什么这样配：按加入时间筛选便于排查某时段的购物车异常
    list_filter = ['created_at']

    # raw_id_fields: 外键弹窗选择字段配置
    # 为什么这样配：user 和 product 表数据量大，下拉框加载性能差，改为弹窗搜索选择
    raw_id_fields = ['user', 'product']


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    """
    订单后台管理

    重点管理类，提供：
        - 订单状态 Badge（@display，按状态分色）
        - 批量发货/批量完成动作（@action）
        - 分组字段配置（fieldsets）
        - 时间层级导航（date_hierarchy）
    """

    # list_display: 列表页展示字段配置
    # 为什么这样配：订单号+用户+金额+状态Badge+创建时间+付款时间
    # 状态 Badge 让订单流转阶段一目了然，便于运营跟进
    list_display = [
        'order_no',
        'user',
        'total_amount',
        'status_badge',
        'created_at',
        'paid_at',
    ]

    # search_fields: 搜索框可搜索字段配置
    # 为什么这样配：订单号是用户与客服沟通的主要凭证，按订单号搜索最精准高效
    search_fields = ['order_no']

    # list_filter: 列表页侧边筛选器配置
    # 为什么这样配：按状态筛选便于跟进不同流转阶段的订单，按创建时间筛选便于按日排查
    list_filter = ['status', 'created_at']

    # fieldsets: 详情页字段分组配置
    # 为什么这样配：订单字段较多，按基础信息/状态流转/时间分组展示逻辑清晰
    fieldsets = (
        # 基础信息组：订单核心数据
        ('基础信息', {
            'fields': ('order_no', 'user', 'total_amount', 'address'),
        }),
        # 状态流转组：订单状态与各阶段时间戳集中展示
        ('状态流转', {
            'fields': ('status', 'paid_at', 'shipped_at', 'completed_at'),
        }),
        # 时间组：创建时间独立分组
        ('时间', {
            'fields': ('created_at',),
        }),
    )

    # readonly_fields: 只读字段配置
    # 为什么这样配：order_no 为系统生成的唯一订单号，人工修改会破坏与支付/物流的关联；
    # created_at/paid_at/shipped_at/completed_at 为系统时间戳，需由业务流程自动写入，人工修改会导致状态流转时间失真
    readonly_fields = ['order_no', 'created_at', 'paid_at', 'shipped_at', 'completed_at']

    # actions: 自定义批量动作配置
    # 为什么这样配：批量发货与批量完成是仓储与售后环节的高频操作
    actions = ['batch_ship', 'batch_complete']

    # raw_id_fields: 外键弹窗选择字段配置
    # 为什么这样配：user 表数据量大，下拉框加载性能差，改为弹窗搜索选择
    raw_id_fields = ['user']

    # date_hierarchy: 时间层级导航配置
    # 为什么这样配：按创建日期提供年/月/日层级钻取导航，便于按时间维度快速定位订单
    date_hierarchy = 'created_at'

    @display(description="状态", ordering="status")
    def status_badge(self, obj):
        """
        @display 装饰器作用：将方法注册为列表页可展示的列，description 指定列标题，ordering 指定排序字段

        订单状态 Badge：按订单状态分色展示，
            - pending（待付款）：黄色（待用户操作）
            - paid（已付款）：蓝色（待发货处理）
            - shipped（已发货）：紫色（物流中）
            - completed（已完成）：绿色（流程结束）
            - cancelled（已取消）：红色（异常终止）
        使用 Tailwind CSS 类名渲染 Badge 样式。
        """
        # 状态到（颜色类、显示文本）的映射表
        status_map = {
            'pending': ('bg-yellow-100 text-yellow-800', '待付款'),
            'paid': ('bg-blue-100 text-blue-800', '已付款'),
            'shipped': ('bg-purple-100 text-purple-800', '已发货'),
            'completed': ('bg-green-100 text-green-800', '已完成'),
            'cancelled': ('bg-red-100 text-red-800', '已取消'),
        }
        # 默认兜底样式，防止出现未定义状态时崩溃
        color_class, text = status_map.get(
            obj.status, ('bg-gray-100 text-gray-800', obj.status)
        )
        # mark_safe 标记 HTML 安全，使用 Tailwind CSS 类名渲染 Badge
        return mark_safe(
            f'<span class="px-2 py-1 rounded-full text-xs font-medium {color_class}">{text}</span>'
        )

    @action(description="批量发货")
    def batch_ship(self, request, queryset):
        """
        @action 装饰器作用：将方法注册为批量动作，description 指定动作显示名称

        批量发货：将选中订单的 status 设为 shipped 并记录 shipped_at 时间，
        适用于已付款订单的批量发货处理场景。
        """
        # update 批量更新状态与发货时间，timezone.now() 保证时间一致性
        updated = queryset.update(status='shipped', shipped_at=timezone.now())
        self.message_user(request, f'成功发货 {updated} 个订单')

    @action(description="批量完成")
    def batch_complete(self, request, queryset):
        """
        @action 装饰器作用：将方法注册为批量动作，description 指定动作显示名称

        批量完成：将选中订单的 status 设为 completed 并记录 completed_at 时间，
        适用于已签收订单的批量完结处理场景。
        """
        # update 批量更新状态与完成时间，timezone.now() 保证时间一致性
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'成功完成 {updated} 个订单')


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    """
    订单明细后台管理

    用于查看订单的商品明细，排查价格快照与规格记录问题。
    订单明细通常通过订单详情页的内联查看，此处提供独立查询入口。
    """

    # list_display: 列表页展示字段配置
    # 为什么这样配：展示所属订单、商品、单价、数量，便于核对订单明细
    list_display = ['order', 'product', 'price', 'quantity']

    # raw_id_fields: 外键弹窗选择字段配置
    # 为什么这样配：order 和 product 表数据量大，下拉框加载性能差，改为弹窗搜索选择
    raw_id_fields = ['order', 'product']


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    """
    收货地址后台管理

    用于查看和管理用户的收货地址，支持默认地址标识和列表页编辑。
    """

    # list_display: 列表页展示字段配置
    # 为什么这样配：展示用户、收货人、电话、完整地址、默认状态、创建时间
    # 默认地址 Badge 让默认地址一目了然，便于客服核对用户地址
    list_display = [
        'user',
        'name',
        'phone',
        'full_address_display',
        'is_default',
        'sort_order',
        'created_at',
    ]

    # search_fields: 搜索框可搜索字段配置
    # 为什么这样配：按收货人姓名和电话搜索便于快速定位用户地址
    search_fields = ['name', 'phone']

    # list_filter: 列表页侧边筛选器配置
    # 为什么这样配：按默认状态筛选便于查看用户的默认地址
    list_filter = ['is_default']

    # list_editable: 列表页可直接编辑字段配置
    # 为什么这样配：sort_order 和 is_default 需要频繁调整，列表内编辑提升效率
    list_editable = ['sort_order', 'is_default']

    # readonly_fields: 只读字段配置
    # 为什么这样配：created_at 和 updated_at 为系统时间戳，由数据库自动维护
    readonly_fields = ['created_at', 'updated_at']

    # raw_id_fields: 外键弹窗选择字段配置
    # 为什么这样配：user 表数据量大，下拉框加载性能差，改为弹窗搜索选择
    raw_id_fields = ['user']

    @display(description="完整地址", ordering=None)
    def full_address_display(self, obj):
        """
        完整地址展示：在列表页展示省市区+详细地址的完整地址字符串
        """
        return obj.full_address

    @display(description="默认", boolean=True, ordering="is_default")
    def is_default_badge(self, obj):
        """
        默认地址 Badge：直观展示地址是否为默认地址
        """
        return obj.is_default
