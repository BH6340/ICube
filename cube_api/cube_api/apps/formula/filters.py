# -*- coding: utf-8 -*-
"""
公式库过滤器

该模块定义了公式列表的自定义过滤器，支持多值过滤。

设计特点：
    - 难度等级支持多值过滤（逗号分隔）
    - 支持按分类、是否自定义过滤
"""
import django_filters
from .models import Formula


class FormulaFilter(django_filters.FilterSet):
    """
    公式过滤器

    扩展默认过滤器，支持难度等级和作者的多值过滤。

    自定义字段：
        - difficulty: 支持多值过滤（使用 BaseInFilter）
        - created_by: 支持按作者ID过滤（使用 NumberInFilter 支持多值）

    支持的过滤字段：
        - category: 分类ID
        - is_custom: 是否自定义公式
        - difficulty: 难度等级（支持逗号分隔多个值）
        - created_by: 作者ID（支持逗号分隔多个值）

    使用示例：
        /api/formulas/?difficulty=1,2,3&is_custom=true&created_by=1,2
    """
    # 难度等级支持多值过滤（逗号分隔）
    difficulty = django_filters.BaseInFilter(field_name='difficulty', lookup_expr='in')
    # 作者支持多值过滤（逗号分隔多个作者ID）
    created_by = django_filters.BaseInFilter(field_name='created_by', lookup_expr='in')

    class Meta:
        model = Formula
        fields = ['category', 'is_custom', 'difficulty', 'created_by']