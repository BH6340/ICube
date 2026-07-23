# -*- coding: utf-8 -*-
"""
公式库模型层

该模块定义了魔方公式库的核心数据模型，包括：
    - 魔方分类（阶数、求解方法、阶段）
    - 魔方状态（目标状态定义）
    - 公式（公式名称、记号、逆公式、前置状态等）
    - 公式标签和标签关联
    - 公式收藏

设计特点：
    - **分类层级**：阶数 → 求解方法 → 阶段，构成三维分类体系
    - **状态定义**：使用 JSONField 存储魔方状态，支持任意阶数
    - **逆公式自动生成**：保存公式时自动生成逆公式
    - **前置状态推导**：支持从目标状态和逆公式推导前置状态
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CubeCategory(models.Model):
    """
    魔方分类模型

    定义魔方公式的分类体系，采用三维分类：阶数、求解方法、阶段。

    字段设计：
        - order: 魔方阶数（3=三阶、4=四阶等）
        - method: 求解方法（如 CFOP、层先法、桥式法等）
        - phase: 阶段（如 Cross、F2L、OLL、PLL 等）
        - name: 分类名称（展示用）
        - sort_order: 排序字段

    唯一性约束：
        - unique_together: 同一阶数、同一方法、同一阶段只能有一个分类
    """
    order = models.IntegerField('阶数', default=3)
    method = models.CharField('求解方法', max_length=50)
    phase = models.CharField('阶段', max_length=50)
    name = models.CharField('分类名称', max_length=100)
    description = models.TextField('描述', blank=True)
    sort_order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'formula'
        db_table = 'formula_cube_category'
        unique_together = ['order', 'method', 'phase']
        ordering = ['order', 'method', 'sort_order']

    def __str__(self):
        return f"{self.order}阶 {self.method} {self.phase}"


class CubeState(models.Model):
    """
    魔方状态模型

    定义魔方的目标状态，用于公式匹配和状态验证。

    状态定义格式（JSON）：
    {
        "order": 3,
        "blocks": [
            {
                "pos": [0, 1, 0],
                "faces": {"U": "Y", "R": "-", "F": "-", "D": "-", "L": "-", "B": "-"}
            }
        ]
    }

    字段设计：
        - name: 状态名称（如 "OLL-01"、"PLL-A"）
        - state_definition: JSON 格式的状态定义
        - category: 关联的分类（可选）

    state_definition 结构：
        - order: 魔方阶数
        - blocks: 块列表，每个块包含位置(pos)和各面颜色(faces)
        - pos: [x, y, z] 坐标，范围 [-half, half]
        - faces: {"U": "Y", "R": "R", ...} 六个面的颜色
    """
    name = models.CharField('状态名称', max_length=100, unique=True)
    state_definition = models.JSONField('状态定义')
    description = models.TextField('描述', blank=True)
    category = models.ForeignKey(
        'CubeCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='states'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'formula'
        db_table = 'formula_cube_state'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class Formula(models.Model):
    """
    公式模型

    定义魔方公式的核心数据，包括公式记号、逆公式、状态匹配等。

    设计特点：
        - **逆公式自动生成**：保存时自动生成逆公式
        - **前置状态推导**：支持从目标状态推导前置状态
        - **自定义公式**：支持用户创建自定义公式
        - **难度等级**：支持难度分级

    字段设计：
        - notation: 公式记号（如 "R U R' U'"）
        - inverse_notation: 逆公式（自动生成）
        - target_state: 目标状态（应用公式后的状态）
        - pre_state_definition: 前置状态定义（应用公式前的状态）
        - is_custom: 是否为用户自定义公式
        - created_by: 创建者（仅自定义公式有值）
    """
    category = models.ForeignKey(
        'CubeCategory',
        on_delete=models.CASCADE,
        related_name='formulas',
        null=True,
        blank=True
    )
    name = models.CharField('公式名称', max_length=200)
    notation = models.TextField('公式记号')
    inverse_notation = models.TextField('逆公式', blank=True)

    target_state = models.ForeignKey(
        'CubeState',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_formulas'
    )
    pre_state_definition = models.JSONField('前置状态定义', null=True, blank=True)

    thumbnail = models.ImageField(
        '缩略图',
        upload_to='formula_thumbnails/',
        null=True,
        blank=True
    )
    difficulty = models.IntegerField('难度等级', default=1)
    description = models.TextField('描述', blank=True)
    view_count = models.IntegerField('浏览次数', default=0)

    is_custom = models.BooleanField('是否自定义', default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='custom_formulas'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'formula'
        db_table = 'formula_formula'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.category} - {self.name}"

    def save(self, *args, **kwargs):
        """
        保存公式

        重写 save 方法，实现逆公式自动生成。

        自动生成逻辑：
            - 如果 notation 存在且 inverse_notation 为空
            - 调用 FormulaService.generate_inverse_notation 生成逆公式
        """
        if self.notation and not self.inverse_notation:
            from .services import FormulaService
            self.inverse_notation = FormulaService.generate_inverse_notation(self.notation)

        super().save(*args, **kwargs)

    def get_pre_state(self):
        """
        获取前置状态定义

        前置状态定义用于公式匹配：
            1. 如果已设置 pre_state_definition，直接返回
            2. 如果有 target_state 和 inverse_notation，从目标状态推导

        Returns:
            前置状态定义（JSON）或 None
        """
        if self.pre_state_definition:
            return self.pre_state_definition

        if self.target_state and self.inverse_notation:
            return {
                'derive_from_target': True,
                'target_state': self.target_state.state_definition,
                'inverse_notation': self.inverse_notation
            }

        return None


class FormulaTag(models.Model):
    """
    公式标签模型

    用于对公式进行分类和标记，支持自定义颜色。

    字段设计：
        - name: 标签名称，唯一
        - color: 标签颜色（十六进制）

    设计原因：
        - 独立的标签表，便于管理和复用
        - 支持自定义颜色，提升前端展示效果
    """
    name = models.CharField('标签名称', max_length=50, unique=True)
    color = models.CharField('标签颜色', max_length=7, default='#1890ff')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'formula'
        db_table = 'formula_formula_tag'

    def __str__(self):
        return self.name


class FormulaTagRelation(models.Model):
    """
    公式-标签关联中间模型

    自定义中间表，支持公式和标签的多对多关系。

    设计原因：
        - 自定义中间表便于后续扩展额外字段
        - 提供清晰的反向访问名

    唯一性约束：
        - unique_together: 同一公式不能重复关联同一标签
    """
    formula = models.ForeignKey(
        'Formula',
        on_delete=models.CASCADE,
        related_name='tag_relations'
    )
    tag = models.ForeignKey(
        'FormulaTag',
        on_delete=models.CASCADE,
        related_name='formula_relations'
    )

    class Meta:
        app_label = 'formula'
        db_table = 'formula_formula_tag_relation'
        unique_together = ['formula', 'tag']


class FormulaCollection(models.Model):
    """
    公式收藏模型

    记录用户收藏公式的操作，支持幂等性。

    字段设计：
        - user: 收藏的用户
        - formula: 被收藏的公式
        - created_at: 收藏时间

    唯一性约束：
        - unique_together: 同一用户对同一公式只能收藏一次

    设计原因：
        - 独立的收藏记录表，便于查询用户收藏列表
        - 与 Formula 的收藏功能配合使用
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='formula_collections')
    formula = models.ForeignKey('Formula', on_delete=models.CASCADE, related_name='collections')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'formula'
        db_table = 'formula_formula_collection'
        unique_together = ['user', 'formula']