# -*- coding: utf-8 -*-
"""
首页导航菜单后台

基于 django-unfold 定制导航菜单管理界面，提供：
    - 分类 Badge：主导航/个人中心导航以颜色标签区分
    - 搜索过滤：支持按标识、名称、路径搜索，按分类筛选
    - 排序编辑：sort_order 可在列表页直接编辑

技术要点：
    - 继承 unfold.admin.ModelAdmin 获取 Tailwind CSS 样式
    - 使用 @display 装饰器自定义分类 Badge 列
"""
from django.contrib import admin
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import NavigationMenu


@admin.register(NavigationMenu)
class NavigationMenuAdmin(ModelAdmin):
    """
    导航菜单管理 Admin

    特色功能：
        - 分类 Badge：主导航(蓝色) / 个人中心导航(紫色) 直观区分
        - 列表页可编辑排序：sort_order 字段可在列表页直接修改
        - 多字段搜索：支持按唯一标识、菜单名称、跳转路径模糊搜索
    """

    # ==================== 列表页配置 ====================

    # list_display：列表页显示的字段集合
    # 配置原因：index 是菜单的唯一标识放首位，category_badge 用颜色区分分类
    # match_paths 是 JSON 数组，直接展示原始格式供管理员核对
    list_display = (
        "index",            # 菜单唯一标识（如 "1"、"p-1"）
        "label",            # 菜单显示名称
        "path",             # 前端路由路径
        "category_badge",   # 自定义列：分类 Badge 标签
        "sort_order",       # 排序值
        "match_paths",      # 路由匹配路径集（JSON 数组）
    )

    # list_editable：列表页可直接编辑的字段（无需进入详情页）
    # 配置原因：管理员需要频繁调整菜单排序，列表页直接编辑效率更高
    # 注意：list_editable 中的字段不能同时出现在 list_display_links 中
    list_editable = ("sort_order",)

    # list_display_links：可点击跳转详情页的字段
    # 配置原因：点击 index 进入编辑页，其他字段仅展示
    list_display_links = ("index",)

    # search_fields：搜索框支持的模糊搜索字段
    # 配置原因：管理员可能通过标识、名称或路径任一字段查找菜单
    search_fields = ("index", "label", "path")

    # list_filter：侧边栏过滤器
    # 配置原因：按分类筛选菜单，区分主导航和个人中心导航
    list_filter = ("category",)

    # ordering：列表默认排序
    # 配置原因：按 sort_order 升序排列，与前端展示顺序一致
    ordering = ("sort_order",)

    # ==================== 自定义列（@display 装饰器） ====================

    @display(description="分类")
    def category_badge(self, obj):
        """
        菜单分类 Badge 标签

        将 category 字段渲染为彩色 Badge：
            - main（主导航栏）：蓝色 Badge
            - profile（个人中心导航栏）：紫色 Badge

        技术要点：
            - 使用 Tailwind CSS 调色板类名
            - get_category_display() 获取 choices 的显示名称
            - mark_safe 确保 HTML 标签不被转义

        Args:
            obj: NavigationMenu 模型实例

        Returns:
            HTML span 标签字符串
        """
        if obj.category == "main":
            # 主导航栏：蓝色 Badge
            return mark_safe(
                '<span class="px-2 py-1 text-xs font-medium rounded-full '
                'bg-blue-100 text-blue-800">主导航栏</span>'
            )
        # 个人中心导航栏：紫色 Badge
        return mark_safe(
            '<span class="px-2 py-1 text-xs font-medium rounded-full '
            'bg-purple-100 text-purple-800">个人中心导航栏</span>'
        )
