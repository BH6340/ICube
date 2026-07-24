# -*- coding: utf-8 -*-
"""
计时器后台

基于 django-unfold 定制计时记录管理界面，提供：
    - 类型 Badge：魔方类型和还原方法以颜色标签直观展示
    - 时间格式化：毫秒数转换为 MM:SS.mmm 可读格式
    - 日期层级导航：支持按创建日期快速跳转

技术要点：
    - 继承 unfold.admin.ModelAdmin 获取 Tailwind CSS 样式
    - 使用 @display 装饰器自定义格式化列和 Badge 列
    - date_hierarchy 提供日期层级导航（Unfold 样式优于原生 Django Admin）
"""
from django.contrib import admin
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import TimerRecord


@admin.register(TimerRecord)
class TimerRecordAdmin(ModelAdmin):
    """
    计时记录管理 Admin

    特色功能：
        - 魔方类型 Badge：二阶/三阶/四阶/五阶 以不同颜色标签区分
        - 还原方法 Badge：层先法/CFOP/桥式/ZBLL 以不同颜色标签区分
        - 时间格式化：毫秒数转换为 MM:SS.mmm 可读格式展示
        - 日期层级导航：按创建日期层级浏览记录
    """

    # ==================== 列表页配置 ====================

    # list_display：列表页显示的字段集合
    # 配置原因：用户和魔方类型放首位便于识别，formatted_time 提供可读时间
    # cube_type_badge 和 method_badge 用颜色区分不同类型和方法
    list_display = (
        "user",                 # 记录所属用户
        "cube_type_badge",      # 自定义列：魔方类型 Badge
        "method_badge",         # 自定义列：还原方法 Badge
        "formatted_time",       # 自定义列：格式化后的时间（MM:SS.mmm）
        "created_at",           # 创建时间
    )

    # search_fields：搜索框支持的模糊搜索字段
    # 配置原因：按用户名搜索计时记录，使用双下划线跨表查询
    # user__username 表示关联 User 表的 username 字段
    search_fields = ("user__username",)

    # list_filter：侧边栏过滤器
    # 配置原因：魔方类型和还原方法是核心筛选维度，创建时间用于按时间段筛选
    list_filter = (
        "cube_type",    # 魔方类型筛选
        "method",       # 还原方法筛选
        "created_at",   # 创建时间筛选
    )

    # date_hierarchy：日期层级导航
    # 配置原因：计时记录按时间维度浏览最自然，提供年→月→日的层级钻取导航
    # Unfold 的 date_hierarchy 样式比原生 Django Admin 更现代化
    date_hierarchy = "created_at"

    # ordering：列表默认排序
    # 配置原因：最新记录排在最前，便于查看最近的计时数据
    ordering = ("-created_at",)

    # list_select_related：预加载关联表
    # 配置原因：每条记录都关联 user，预加载避免 N+1 查询问题
    # user 是外键，select_related 会在单条 SQL 中 JOIN 加载
    list_select_related = ("user",)

    # ==================== 自定义列（@display 装饰器） ====================

    @display(
        description="魔方类型",
        # ordering：支持按该列排序时对应的数据库字段
        ordering="cube_type",
    )
    def cube_type_badge(self, obj):
        """
        魔方类型 Badge 标签

        将 cube_type 字段渲染为彩色 Badge：
            - 2x2：青色 Badge
            - 3x3：蓝色 Badge（默认类型，最常见）
            - 4x4：绿色 Badge
            - 5x5：橙色 Badge
            - other：灰色 Badge

        技术要点：
            - 使用字典映射类型到颜色，便于维护
            - get_cube_type_display() 获取 choices 的中文显示名称
            - mark_safe 确保 HTML 标签不被转义

        Args:
            obj: TimerRecord 模型实例

        Returns:
            HTML span 标签字符串
        """
        # 类型到 Tailwind CSS 颜色类的映射
        color_map = {
            "2x2": "bg-cyan-100 text-cyan-800",
            "3x3": "bg-blue-100 text-blue-800",
            "4x4": "bg-green-100 text-green-800",
            "5x5": "bg-orange-100 text-orange-800",
            "other": "bg-gray-100 text-gray-800",
        }
        # 获取对应的颜色类，默认使用灰色
        color_class = color_map.get(obj.cube_type, "bg-gray-100 text-gray-800")
        # get_cube_type_display() 返回 choices 的显示值（如 "三阶魔方"）
        return mark_safe(
            f'<span class="px-2 py-1 text-xs font-medium rounded-full {color_class}">'
            f'{obj.get_cube_type_display()}</span>'
        )

    @display(
        description="还原方法",
        ordering="method",
    )
    def method_badge(self, obj):
        """
        还原方法 Badge 标签

        将 method 字段渲染为彩色 Badge：
            - layer（层先法）：绿色 Badge
            - cfop（CFOP）：紫色 Badge
            - roux（桥式）：黄色 Badge
            - zbll（ZBLL）：红色 Badge
            - other（其他）：灰色 Badge

        Args:
            obj: TimerRecord 模型实例

        Returns:
            HTML span 标签字符串
        """
        color_map = {
            "layer": "bg-green-100 text-green-800",
            "cfop": "bg-purple-100 text-purple-800",
            "roux": "bg-amber-100 text-amber-800",
            "zbll": "bg-red-100 text-red-800",
            "other": "bg-gray-100 text-gray-800",
        }
        color_class = color_map.get(obj.method, "bg-gray-100 text-gray-800")
        return mark_safe(
            f'<span class="px-2 py-1 text-xs font-medium rounded-full {color_class}">'
            f'{obj.get_method_display()}</span>'
        )

    @display(
        description="还原时间",
        # ordering：支持按该列排序时对应的数据库字段
        ordering="time_ms",
    )
    def formatted_time(self, obj):
        """
        格式化还原时间

        将毫秒数转换为 MM:SS.mmm 可读格式。
        例如：123456 ms → 02:03.456

        技术要点：
            - 数据库存储毫秒整数（time_ms），避免浮点精度问题
            - 列表页展示时转换为可读格式，提升管理员体验
            - 使用 divmod 分离分钟和秒数

        Args:
            obj: TimerRecord 模型实例

        Returns:
            格式化后的时间字符串（MM:SS.mmm）
        """
        # 将毫秒转换为分钟和剩余毫秒
        minutes, remainder = divmod(obj.time_ms, 60000)
        # 将剩余毫秒转换为秒和毫秒
        seconds, milliseconds = divmod(remainder, 1000)
        # 格式化为 MM:SS.mmm（分钟和秒补零到 2 位，毫秒补零到 3 位）
        return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
