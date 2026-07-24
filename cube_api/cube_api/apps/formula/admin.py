# -*- coding: utf-8 -*-
"""
公式库后台管理模块（基于 django-unfold）

该模块为公式库的所有模型注册 Unfold 风格的后台管理界面，
提供列表展示、筛选、搜索、行内编辑、只读保护、可视化 Badge 等能力。

依赖说明：
    - unfold.admin.ModelAdmin：替换 Django 默认 ModelAdmin，提供更现代的 UI
    - unfold.decorators.display：替代 admin.display，用于自定义列展示
    - unfold.decorators.action：替代 admin.action，用于自定义批量操作（本文件未使用但保留导入）
"""
from django.contrib import admin
from django.utils.safestring import mark_safe

from unfold.admin import ModelAdmin
from unfold.decorators import display, action

from .models import (
    CubeCategory,
    CubeState,
    Formula,
    FormulaTag,
    FormulaTagRelation,
    FormulaCollection,
)


@admin.register(CubeCategory)
class CubeCategoryAdmin(ModelAdmin):
    """
    魔方分类后台管理

    管理魔方公式的三维分类体系（阶数 → 求解方法 → 阶段）。
    支持 sort_order 的行内编辑，便于快速调整分类排序。
    """

    # list_display：列表页展示的字段
    # Why：覆盖默认展示，让管理员一眼看到分类的关键维度（阶数/方法/阶段）与排序
    list_display = ('id', 'name', 'order', 'method', 'phase', 'sort_order', 'created_at')

    # list_filter：右侧筛选器
    # Why：按阶数/方法/阶段三个维度筛选，快速定位某一类公式集合
    list_filter = ('order', 'method', 'phase')

    # search_fields：搜索框可检索字段
    # Why：分类名称与维度均支持模糊搜索，提升查找效率
    search_fields = ('name', 'method', 'phase')

    # list_editable：可在列表页直接编辑的字段
    # Why：sort_order 需要频繁调整，行内编辑免去逐条进入详情页的麻烦
    list_editable = ('sort_order',)

    # ordering：默认排序
    # Why：与模型 Meta 保持一致，按阶数 → 方法 → 排序值展示，符合分类层级直觉
    ordering = ('order', 'method', 'sort_order')


@admin.register(CubeState)
class CubeStateAdmin(ModelAdmin):
    """
    魔方状态后台管理

    管理魔方的目标状态定义（JSON 格式）。state_definition 体量较大且为结构化数据，
    因此不在列表展示，仅展示名称与所属分类。
    """

    # list_display：列表页展示字段
    # Why：状态定义 JSON 过长不适合列表展示，仅展示名称/分类/创建时间即可识别
    list_display = ('id', 'name', 'category', 'created_at')

    # list_filter：按分类筛选
    # Why：状态数量多时，按所属分类筛选可快速缩小范围
    list_filter = ('category',)

    # search_fields：按名称搜索
    # Why：状态名称（如 OLL-01）是唯一可读标识，支持搜索便于精确定位
    search_fields = ('name',)

    # raw_id_fields：分类使用弹窗式外键选择器
    # Why：分类数量较多时下拉框体验差，raw_id 改为搜索弹窗，提升选择效率
    raw_id_fields = ('category',)


@admin.register(Formula)
class FormulaAdmin(ModelAdmin):
    """
    公式后台管理（核心模型）

    提供公式的完整管理能力，包括：
        - 难度 Badge 可视化（基础/进阶/困难）
        - 自定义公式标识
        - 逆公式只读保护（由 save() 自动生成）
        - 浏览量只读保护（由系统统计）
        - 分组字段配置（基础信息/状态配置/统计）
    """

    # list_display：列表页展示字段
    # Why：用自定义 @display 方法渲染难度 Badge 和自定义标识，比纯数字更直观
    list_display = (
        'id',
        'thumbnail_preview',
        'name',
        'category',
        'difficulty_badge',
        'is_custom_badge',
        'view_count',
        'created_by',
        'created_at',
    )

    # search_fields：可搜索字段
    # Why：管理员通常按公式名称或公式记号定位公式，这两项是最常用的检索入口
    search_fields = ('name', 'notation')

    # list_filter：筛选维度
    # Why：按分类/难度/是否自定义筛选，覆盖最常见的运营筛选场景
    list_filter = ('category', 'difficulty', 'is_custom')

    # fieldsets：详情页表单分组
    # Why：字段较多，分组展示降低认知负担；按"基础信息→状态配置→统计"逻辑递进
    fieldsets = (
        # 基础信息：公式的核心属性，编辑频率最高
        ('基础信息', {
            'fields': ('category', 'name', 'notation', 'inverse_notation', 'difficulty', 'description'),
        }),
        # 状态配置：公式与状态/自定义属性的关联，影响公式匹配逻辑
        ('状态配置', {
            'fields': ('target_state', 'pre_state_definition', 'is_custom', 'created_by'),
        }),
        # 统计：运营数据与缩略图，通常只读或低频编辑
        ('统计', {
            'fields': ('view_count', 'thumbnail'),
        }),
    )

    # readonly_fields：只读字段
    # Why：
    #   - inverse_notation：由 Formula.save() 调用 FormulaService 自动生成，手动编辑会被覆盖
    #   - view_count：由系统统计累加，人工修改会导致数据失真
    readonly_fields = ('inverse_notation', 'view_count')

    # raw_id_fields：外键使用弹窗选择器
    # Why：目标状态/创建者/分类记录数较多，raw_id 避免长下拉框，改用搜索弹窗
    raw_id_fields = ('target_state', 'created_by', 'category')

    @display(description='缩略图')
    def thumbnail_preview(self, obj):
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            return mark_safe(
                f'<img src="{obj.thumbnail.url}" style="max-width:60px;max-height:60px;object-fit:cover;border-radius:4px;" />'
            )
        return '暂无图片'

    @display(
        description='难度',
        ordering='difficulty',
    )
    def difficulty_badge(self, obj):
        """
        难度 Badge 自定义列

        作用：将数字难度渲染为带颜色的 Badge，便于快速识别难度区间。
        规则：
            - 1-6  基础（蓝色 bg-blue-100/text-blue-800）
            - 7-11 进阶（黄色 bg-amber-100/text-amber-800）
            - 12+  困难（红色 bg-red-100/text-red-800）
        """
        if obj.difficulty is None:
            return '-'

        # 根据难度区间选择 Tailwind 配色
        if obj.difficulty <= 6:
            # 基础：蓝色，表示入门难度
            bg_class, text_class, label = 'bg-blue-100', 'text-blue-800', '基础'
        elif obj.difficulty <= 11:
            # 进阶：黄色，表示中等难度
            bg_class, text_class, label = 'bg-amber-100', 'text-amber-800', '进阶'
        else:
            # 困难：红色，表示高难度
            bg_class, text_class, label = 'bg-red-100', 'text-red-800', '困难'

        # mark_safe：标记 HTML 为安全，避免 Django 转义导致 Badge 无法渲染
        return mark_safe(
            f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {bg_class} {text_class}">'
            f'{obj.difficulty} · {label}'
            f'</span>'
        )

    @display(
        description='自定义',
        # boolean=True：渲染为图标而不是文本
        # Why：布尔值用对勾/叉号展示比 True/False 文本更直观
        boolean=True,
    )
    def is_custom_badge(self, obj):
        """
        自定义公式标识列

        作用：以布尔图标标识公式是否为用户自定义，便于区分官方公式与 UGC 内容。
        """
        return obj.is_custom


@admin.register(FormulaTag)
class FormulaTagAdmin(ModelAdmin):
    """
    公式标签后台管理

    管理标签及其颜色。color 字段以颜色色块形式预览，方便确认标签配色。
    """

    # list_display：列表展示字段
    # Why：通过 color_badge 方法渲染颜色色块，比纯文本色值更直观
    list_display = ('id', 'name', 'color_badge', 'created_at')

    # search_fields：按名称搜索
    # Why：标签按名称唯一定位，搜索是最快的查找方式
    search_fields = ('name',)

    @display(description='颜色')
    def color_badge(self, obj):
        """
        标签颜色预览列

        作用：将标签颜色渲染为带圆角背景的色块，并展示色值，
        便于管理员在列表页直接确认标签配色是否合理。
        """
        if not obj.color:
            return '-'

        # mark_safe：标记 HTML 安全，渲染色块样式
        return mark_safe(
            f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" '
            f'style="background-color: {obj.color}; color: #ffffff;">'
            f'{obj.color}'
            f'</span>'
        )


@admin.register(FormulaTagRelation)
class FormulaTagRelationAdmin(ModelAdmin):
    """
    公式-标签关联后台管理

    管理公式与标签的多对多关联记录。
    """

    # list_display：列表展示字段
    # Why：展示关联两端（公式/标签），一眼看清哪条公式打了哪个标签
    list_display = ('id', 'formula', 'tag')

    # list_filter：按标签筛选
    # Why：运营常按标签维度查看公式集合，标签数量可控适合做筛选器
    list_filter = ('tag',)

    # raw_id_fields：外键弹窗选择器
    # Why：公式与标签记录数都较多，raw_id 避免长下拉框
    raw_id_fields = ('formula', 'tag')


@admin.register(FormulaCollection)
class FormulaCollectionAdmin(ModelAdmin):
    """
    公式收藏后台管理

    记录用户对公式的收藏行为，用于运营分析与数据统计。
    """

    # list_display：列表展示字段
    # Why：展示用户/公式/收藏时间，构成收藏记录的完整可读信息
    list_display = ('id', 'user', 'formula', 'created_at')

    # list_filter：按用户筛选
    # Why：运营常按用户维度查看其收藏列表，定位特定用户的收藏行为
    list_filter = ('user',)

    # raw_id_fields：外键弹窗选择器
    # Why：用户与公式记录数都较多，raw_id 避免长下拉框，提升选择效率
    raw_id_fields = ('user', 'formula')
