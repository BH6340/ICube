# -*- coding: utf-8 -*-
"""
公式库序列化器层

该模块定义了公式库相关模型的序列化器，负责数据的序列化和反序列化。

设计特点：
    - **多序列化器策略**：列表和详情使用不同的序列化器
    - **状态验证**：魔方状态定义通过 CubeStateService 验证
    - **标签处理**：支持 tag_ids 字段批量关联标签
    - **缩略图处理**：统一使用 build_image_url 生成完整URL
    - **自定义公式**：自动识别用户创建的自定义公式
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.conf import settings
from django.core.files.storage import default_storage

from .models import CubeCategory, CubeState, Formula, FormulaTag, FormulaTagRelation, FormulaCollection
from .services import CubeStateService


class CubeCategorySerializer(serializers.ModelSerializer):
    """
    魔方分类序列化器

    序列化魔方分类数据，包含完整的分类信息。

    字段：
        - id: 分类ID
        - order: 阶数
        - method: 求解方法
        - phase: 阶段
        - name: 分类名称
        - description: 描述
        - sort_order: 排序
        - created_at: 创建时间
    """

    class Meta:
        model = CubeCategory
        fields = ('id', 'order', 'method', 'phase', 'name', 'description', 'sort_order', 'created_at')


class CubeStateSerializer(serializers.ModelSerializer):
    """
    魔方状态序列化器

    序列化魔方状态数据，包含状态定义的验证。

    字段：
        - id: 状态ID
        - name: 状态名称
        - state_definition: 状态定义（JSON）
        - description: 描述
        - category: 关联分类
        - created_at: 创建时间（只读）

    验证逻辑：
        - state_definition 通过 CubeStateService 验证，确保格式正确
    """

    class Meta:
        model = CubeState
        fields = ('id', 'name', 'state_definition', 'description', 'category', 'created_at')
        read_only_fields = ('created_at',)

    def validate_state_definition(self, value):
        """
        验证状态定义的正确性

        使用 CubeStateService 进行多层次验证。

        Args:
            value: 状态定义（JSON）

        Raises:
            ValidationError: 验证失败时抛出

        Returns:
            验证通过的状态定义
        """
        errors = CubeStateService.validate_state_definition(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value


class FormulaTagSerializer(serializers.ModelSerializer):
    """
    公式标签序列化器

    序列化公式标签数据，包含标签名称和颜色。

    字段：
        - id: 标签ID
        - name: 标签名称
        - color: 标签颜色
        - created_at: 创建时间（只读）
    """

    class Meta:
        model = FormulaTag
        fields = ('id', 'name', 'color', 'created_at')
        read_only_fields = ('created_at',)


class FormulaListSerializer(serializers.ModelSerializer):
    """
    公式列表序列化器（轻量级）

    用于公式列表展示，只包含必要字段，减少数据传输量。

    设计原因：
        - 列表页不需要完整的状态定义，轻量级序列化器提高加载速度
        - 不含前置状态定义，减少网络带宽消耗

    字段：
        - id: 公式ID
        - name: 公式名称
        - notation: 公式记号
        - inverse_notation: 逆公式
        - category: 分类（嵌套序列化）
        - target_state: 目标状态（嵌套序列化）
        - difficulty: 难度等级
        - thumbnail: 缩略图URL（动态生成）
        - is_custom: 是否自定义
        - tags: 标签列表（嵌套序列化）
        - view_count: 浏览次数
        - created_at: 创建时间
    """
    category = CubeCategorySerializer(read_only=True)
    target_state = CubeStateSerializer(read_only=True)
    tags = FormulaTagSerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Formula
        fields = (
            'id', 'name', 'notation', 'inverse_notation', 'category', 'target_state',
            'difficulty', 'thumbnail', 'is_custom', 'tags', 'view_count', 'created_at'
        )

    def get_thumbnail(self, obj):
        """
        生成缩略图URL

        使用 build_image_url 工具函数，统一处理图片URL的生成逻辑。

        Args:
            obj: Formula 对象

        Returns:
            完整的缩略图URL或空字符串
        """
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.thumbnail)


class FormulaSerializer(serializers.ModelSerializer):
    """
    公式详情序列化器

    用于公式详情展示，包含完整信息和动态字段。

    设计特点：
        - 包含完整的状态定义
        - 动态计算前置状态（pre_state）
        - 支持 tag_ids 字段批量关联标签
        - 自动识别用户创建的自定义公式

    动态字段：
        - pre_state: 前置状态定义（从目标状态推导或直接返回）
        - thumbnail: 缩略图URL（动态生成）

    只读字段：
        - inverse_notation: 逆公式（自动生成）
        - created_at: 创建时间
        - is_custom: 是否自定义
        - view_count: 浏览次数
    """
    category = CubeCategorySerializer(read_only=True)
    target_state = CubeStateSerializer(read_only=True)
    tags = FormulaTagSerializer(many=True, read_only=True)
    pre_state = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    # 用于批量关联标签的写入字段
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='标签ID列表'
    )

    class Meta:
        model = Formula
        fields = (
            'id', 'name', 'notation', 'inverse_notation', 'category', 'target_state',
            'pre_state_definition', 'pre_state', 'thumbnail', 'difficulty', 'description',
            'is_custom', 'tags', 'tag_ids', 'view_count', 'created_at'
        )
        read_only_fields = ('inverse_notation', 'created_at', 'is_custom', 'view_count')

    @extend_schema_field(serializers.JSONField)
    def get_pre_state(self, obj):
        """
        获取前置状态定义

        调用 Formula 模型的 get_pre_state 方法，支持从目标状态推导前置状态。

        Args:
            obj: Formula 对象

        Returns:
            前置状态定义（JSON）或 None
        """
        return obj.get_pre_state()

    def get_thumbnail(self, obj):
        """
        生成缩略图URL

        使用 build_image_url 工具函数，统一处理图片URL的生成逻辑。

        Args:
            obj: Formula 对象

        Returns:
            完整的缩略图URL或空字符串
        """
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.thumbnail)

    def validate_pre_state_definition(self, value):
        """
        验证前置状态定义的正确性

        使用 CubeStateService 进行验证，确保状态定义格式正确。

        Args:
            value: 前置状态定义（JSON）

        Raises:
            ValidationError: 验证失败时抛出

        Returns:
            验证通过的状态定义
        """
        if value:
            errors = CubeStateService.validate_state_definition(value)
            if errors:
                raise serializers.ValidationError(errors)
        return value

    def create(self, validated_data):
        """
        创建公式

        处理标签关联、缩略图上传和自定义公式识别。

        自动识别逻辑：
            - 如果当前用户已登录且不是管理员，标记为自定义公式
            - 设置 created_by 为当前用户

        Args:
            validated_data: 验证后的表单数据

        Returns:
            创建的 Formula 对象
        """
        tag_ids = validated_data.pop('tag_ids', [])
        thumbnail_file = validated_data.pop('thumbnail', None)
        request = self.context.get('request')

        # 自动识别自定义公式
        if request and request.user.is_authenticated and not request.user.is_staff:
            validated_data['is_custom'] = True
            validated_data['created_by'] = request.user

        # 处理缩略图上传
        if thumbnail_file:
            saved_path = default_storage.save(f"formula_thumbnails/{thumbnail_file.name}", thumbnail_file)
            validated_data['thumbnail'] = f"{settings.MEDIA_URL}{saved_path}"

        formula = super().create(validated_data)

        # 处理标签关联
        if tag_ids:
            tags = FormulaTag.objects.filter(id__in=tag_ids)
            for tag in tags:
                FormulaTagRelation.objects.get_or_create(formula=formula, tag=tag)

        return formula

    def update(self, instance, validated_data):
        """
        更新公式

        支持标签更新和缩略图上传。

        Args:
            instance: 原 Formula 对象
            validated_data: 更新的数据

        Returns:
            更新后的 Formula 对象
        """
        tag_ids = validated_data.pop('tag_ids', None)
        thumbnail_file = validated_data.pop('thumbnail', None)
        request = self.context.get('request')

        # 处理缩略图上传
        if thumbnail_file:
            saved_path = default_storage.save(f"formula_thumbnails/{thumbnail_file.name}", thumbnail_file)
            validated_data['thumbnail'] = f"{settings.MEDIA_URL}{saved_path}"

        formula = super().update(instance, validated_data)

        # 更新标签关联（先删除后添加）
        if tag_ids is not None:
            FormulaTagRelation.objects.filter(formula=formula).delete()
            tags = FormulaTag.objects.filter(id__in=tag_ids)
            for tag in tags:
                FormulaTagRelation.objects.get_or_create(formula=formula, tag=tag)

        return formula


class FormulaMatchSerializer(serializers.Serializer):
    """
    公式匹配请求序列化器

    用于公式匹配 API 的请求数据验证。

    字段：
        - state_definition: 用户当前的魔方状态（JSON格式）

    验证逻辑：
        - state_definition 通过 CubeStateService 验证，确保格式正确
    """
    state_definition = serializers.JSONField(help_text='用户当前魔方状态')

    def validate_state_definition(self, value):
        """
        验证用户状态定义的正确性

        使用 CubeStateService 进行多层次验证。

        Args:
            value: 用户状态定义（JSON）

        Raises:
            ValidationError: 验证失败时抛出

        Returns:
            验证通过的状态定义
        """
        errors = CubeStateService.validate_state_definition(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value


class FormulaCollectionSerializer(serializers.ModelSerializer):
    """
    公式收藏序列化器

    序列化公式收藏记录，包含收藏的公式详情。

    字段：
        - id: 收藏记录ID
        - formula: 收藏的公式（嵌套序列化）
        - created_at: 创建时间（只读）

    设计特点：
        - 用户字段自动设置为当前用户
        - 使用轻量级的 FormulaListSerializer 序列化公式
    """
    formula = FormulaListSerializer(read_only=True)

    class Meta:
        model = FormulaCollection
        fields = ('id', 'formula', 'created_at')
        read_only_fields = ('created_at',)

    def create(self, validated_data):
        """
        创建收藏记录

        自动设置用户为当前登录用户。

        Args:
            validated_data: 验证后的表单数据

        Returns:
            创建的 FormulaCollection 对象
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)