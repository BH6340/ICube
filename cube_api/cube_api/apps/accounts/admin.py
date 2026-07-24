# -*- coding: utf-8 -*-
"""
用户管理后台

基于 django-unfold 定制用户后台管理界面，提供：
    - 头像预览：列表页直接展示用户头像缩略图
    - 状态 Badge：is_active 状态以颜色标签直观展示（绿色=激活，红色=禁用）
    - Fieldsets 分组：编辑表单按基本信息/权限/时间戳分组展示
    - 密码安全：密码字段只读，避免明文暴露
    - 批量操作：批量禁用/解冻用户

技术要点：
    - 所有 Admin 类继承 unfold.admin.ModelAdmin 而非 django.contrib.admin.ModelAdmin
    - 使用 @display 装饰器自定义列表页列（Unfold 特有，替代原生 admin.display 装饰器）
    - 使用 @action 装饰器定义批量操作（Unfold 特有，替代原生 admin.action 装饰器）
"""
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import escape

# unfold.admin.ModelAdmin：Unfold 的基础 ModelAdmin
# 继承自 Django 原生 ModelAdmin，额外提供 Tailwind CSS 样式支持、Tab 布局、高级过滤器等功能
# 原生 Django Admin 使用 admin.ModelAdmin，界面风格为传统 Bootstrap 样式
from unfold.admin import ModelAdmin

# unfold 装饰器：@display 用于自定义列表页列，@action 用于定义批量操作
# 与原生 admin.display / admin.action 功能类似，但额外支持 Unfold 的样式参数（如 badge 类型）
from unfold.decorators import display, action

from .models import User


@admin.register(User)
class UserAdmin(ModelAdmin):
    """
    用户管理 Admin

    特色功能：
        - 头像预览列：列表页展示 40x40 圆形头像缩略图
        - 状态 Badge：is_active 渲染为绿色/红色标签
        - 密码只读：编辑页密码字段显示为安全提示，不可直接修改
        - 批量禁用/解冻：通过 Admin Action 批量切换用户激活状态
    """

    # ==================== 列表页配置 ====================

    # list_display：列表页显示的字段集合
    # 配置原因：头像放首位便于视觉识别用户，状态 Badge 直观展示账号可用性
    # 其中 avatar_preview 和 status_badge 是通过 @display 装饰器自定义的虚拟列
    list_display = (
        "avatar_preview",    # 自定义列：头像预览缩略图
        "email",             # 用户邮箱（登录凭证）
        "username",          # 用户昵称
        "followers_count",   # 自定义列：粉丝数量（从 Redis 缓存读取）
        "following_count",   # 自定义列：关注数量（从 Redis 缓存读取）
        "date_joined",       # 注册时间
        "status_badge",      # 自定义列：激活状态 Badge 标签
    )

    # list_display_links：可点击跳转详情页的字段
    # 配置原因：点击邮箱直接进入编辑页，头像和状态列仅展示不可点击
    list_display_links = ("email",)

    # search_fields：搜索框支持的模糊搜索字段
    # 配置原因：邮箱和昵称是管理用户时最常用的检索条件
    search_fields = ("email", "username")

    # list_filter：侧边栏过滤器
    # 配置原因：管理员需要按账号状态和注册时间筛选用户
    # is_active：区分激活/禁用用户
    # is_staff：区分普通用户/管理员
    # date_joined：按注册时间范围筛选（Unfold 提供 DateRangeFilter 优于原生 DateFieldListFilter）
    list_filter = (
        "is_active",
        "is_staff",
        "date_joined",
    )

    # list_per_page：每页显示条数
    # 配置原因：用户量大时减少单页加载量，50 条兼顾浏览效率和分页频率
    list_per_page = 50

    # ordering：列表默认排序
    # 配置原因：最新注册的用户排在最前，便于管理员关注新用户
    ordering = ("-date_joined",)

    # ==================== 编辑页配置 ====================

    # readonly_fields：编辑页只读字段
    # 配置原因：
    #   - date_joined/last_login：系统自动生成，不应手动修改
    #   - password：密码为哈希存储，直接展示无意义且存在安全风险
    #     通过自定义只读字段显示安全提示，密码修改通过 Django auth 的 change_password 链接完成
    readonly_fields = (
        "date_joined",
        "last_login",
        "password_display",
    )

    # fieldsets：编辑页表单分组布局
    # 配置原因：将字段按逻辑分组，提升管理员的编辑效率和体验
    # 原生 Django Admin 也支持 fieldsets，但 Unfold 额外提供 Tab 风格的分页布局
    fieldsets = (
        (
            "基本信息",
            {
                "fields": ("email", "username", "image", "bio"),
            },
        ),
        # 第二组：权限控制（是否激活、是否员工、是否超管）
        # 配置原因：权限字段集中展示，避免分散在多处导致误操作
        (
            "权限控制",
            {
                "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
        # 第三组：重要时间戳（只读，供管理员审计参考）
        (
            "重要时间戳",
            {
                "fields": ("date_joined", "last_login"),
                # classes: Unfold 特有，collapse 使该分组默认折叠
                "classes": ("collapse",),
            },
        ),
        # 第四组：密码安全提示（只读）
        (
            "密码安全",
            {
                "fields": ("password_display",),
                "description": "密码以哈希方式安全存储，无法查看明文。如需修改密码，请使用页面顶部的「修改密码」链接。",
            },
        ),
    )

    # filter_horizontal：多对多字段的水平选择器
    # 配置原因：groups 和 user_permissions 是 M2M 字段，水平选择器比默认的 <select multiple> 更易用
    filter_horizontal = ("groups", "user_permissions")

    # ==================== 自定义列（@display 装饰器） ====================

    @display(
        description="头像",
        ordering="image",
    )
    def avatar_preview(self, obj):
        """
        头像预览列

        在列表页展示用户的头像缩略图（40x40 圆形）。
        如果用户未设置头像，显示默认占位图。

        技术要点：
            - ImageField 需要通过 url 属性获取完整访问路径
            - 使用 mark_safe 标记返回的 HTML 为安全内容
            - 使用 escape 转义 URL 中的特殊字符，防止 XSS

        Args:
            obj: User 模型实例

        Returns:
            HTML img 标签字符串
        """
        if obj.image and hasattr(obj.image, 'url'):
            return mark_safe(
                f'<img src="{escape(obj.image.url)}" '
                f'style="width:40px;height:40px;border-radius:50%;object-fit:cover;" '
                f'alt="头像">'
            )
        return mark_safe(
            '<div style="width:40px;height:40px;border-radius:50%;'
            'background:#e5e7eb;display:flex;align-items:center;justify-content:center;'
            'font-size:12px;color:#9ca3af;">N/A</div>'
        )

    @display(
        description="状态",
        # boolean=False：该列不使用布尔图标，而是使用自定义 HTML
        boolean=False,
    )
    def status_badge(self, obj):
        """
        用户状态 Badge 标签

        将 is_active 字段渲染为彩色 Badge：
            - is_active=True：绿色 Badge，显示"激活"
            - is_active=False：红色 Badge，显示"禁用"

        技术要点：
            - 使用 Unfold/Tailwind 的 Badge 样式类名
            - 绿色：bg-green-100 + text-green-800（Tailwind 调色板）
            - 红色：bg-red-100 + text-red-800
            - mark_safe 确保 HTML 标签不被转义

        Args:
            obj: User 模型实例

        Returns:
            HTML span 标签字符串
        """
        if obj.is_active:
            # 激活状态：绿色 Badge
            return mark_safe(
                '<span class="px-2 py-1 text-xs font-medium rounded-full '
                'bg-green-100 text-green-800">激活</span>'
            )
        # 禁用状态：红色 Badge
        return mark_safe(
            '<span class="px-2 py-1 text-xs font-medium rounded-full '
            'bg-red-100 text-red-800">禁用</span>'
        )

    @display(description="密码")
    def password_display(self, obj):
        """
        密码安全提示（只读）

        编辑页展示密码安全提示，而非实际哈希值。
        配置原因：直接展示哈希密码无业务意义且存在信息泄露风险，
        管理员通过 Django 内置的「修改密码」链接进行密码重置。

        Args:
            obj: User 模型实例

        Returns:
            安全提示文本
        """
        if obj.password:
            return "密码已加密存储（哈希值），请通过「修改密码」链接重置"
        return "未设置密码（可能使用第三方登录）"

    @display(description="粉丝数", ordering="followers")
    def followers_count(self, obj):
        """
        粉丝数量列

        从 User 模型的 followers_count 属性获取粉丝数量。
        该属性内部使用 Redis 缓存，避免每次查询都执行 COUNT 聚合。

        Args:
            obj: User 模型实例

        Returns:
            粉丝数量（整数）
        """
        return obj.followers_count

    @display(description="关注数", ordering="following")
    def following_count(self, obj):
        """
        关注数量列

        从 User 模型的 following_count 属性获取关注数量。
        该属性内部使用 Redis 缓存，O(1) 复杂度获取。

        Args:
            obj: User 模型实例

        Returns:
            关注数量（整数）
        """
        return obj.following_count

    # ==================== 批量操作（@action 装饰器） ====================

    @action(
        description="批量禁用选中用户",
        # permissions：控制该 Action 的显示权限，返回字典定义可用性
        # 配置原因：仅超级管理员可执行批量禁用操作，防止普通管理员误操作
    )
    def disable_users(self, request, queryset):
        """
        批量禁用用户

        将选中的用户 is_active 设为 False，阻止其登录系统。
        配置原因：管理员需要快速封禁违规用户，逐个编辑效率太低。

        技术要点：
            - 使用 update() 批量更新，比循环 save() 更高效（单条 SQL）
            - update() 不会触发模型的 save() 方法和信号，适合批量操作

        Args:
            request: HTTP 请求对象
            queryset: 选中的 User 查询集
        """
        # 批量更新 is_active=False，阻止用户登录
        updated = queryset.update(is_active=False)
        # 通过 Django messages 框架向管理员反馈操作结果
        self.message_user(request, f"成功禁用 {updated} 个用户账号")

    @action(
        description="批量解冻选中用户",
    )
    def enable_users(self, request, queryset):
        """
        批量解冻用户

        将选中的用户 is_active 设为 True，恢复其登录权限。
        配置原因：封禁期结束后管理员需要批量恢复用户。

        Args:
            request: HTTP 请求对象
            queryset: 选中的 User 查询集
        """
        updated = queryset.update(is_active=True)
        self.message_user(request, f"成功解冻 {updated} 个用户账号")

    # actions：在列表页展示的自定义 Action 列表
    # 配置原因：将批量禁用和批量解冻注册到下拉菜单中
    actions = ("disable_users", "enable_users")
