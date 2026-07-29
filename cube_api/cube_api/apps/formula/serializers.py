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
from django.core.files.uploadedfile import InMemoryUploadedFile
import os
import uuid

from .models import CubeCategory, CubeState, Formula, FormulaTag, FormulaTagRelation, FormulaCollection
from .services import CubeStateService
from cube_api.utils.image_processor import process_image


class CubeCategorySerializer(serializers.ModelSerializer):
    """
    魔方分类序列化器

    序列化魔方分类数据，包含完整的分类信息，支持用户自定义分类。

    字段：
        - id: 分类ID
        - order: 阶数
        - method: 求解方法
        - phase: 阶段
        - name: 分类名称
        - description: 描述
        - sort_order: 排序
        - is_custom: 是否用户自定义
        - created_by: 创建者信息（只读）
        - created_at: 创建时间
    """
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = CubeCategory
        fields = ('id', 'order', 'method', 'phase', 'name', 'description', 'sort_order', 
                  'is_custom', 'created_by', 'created_at')
        read_only_fields = ('created_by', 'is_custom', 'created_at')

    def get_created_by(self, obj):
        """获取创建者信息"""
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username
            }
        return None


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


class FormulaSimpleSerializer(serializers.ModelSerializer):
    """
    公式精简序列化器（帖子编辑器专用）

    用于帖子编辑器选择公式时使用，只包含必要字段。

    设计原因：
        - 帖子编辑器只需要公式的基本信息和缩略图
        - 减少数据传输量，提高加载速度

    字段：
        - id: 公式ID
        - name: 公式名称
        - notation: 公式记号
        - category_name: 分类名称（拼接阶数+方法+阶段）
        - thumbnail: 缩略图URL
    """
    category_name = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Formula
        fields = ('id', 'name', 'notation', 'category_name', 'thumbnail')

    def get_category_name(self, obj):
        """
        获取分类名称（拼接阶数+方法+阶段）

        Args:
            obj: Formula 对象

        Returns:
            分类名称字符串
        """
        if obj.category:
            return f"{obj.category.order}阶 {obj.category.method} {obj.category.phase}"
        return ''

    def get_thumbnail(self, obj):
        """
        生成缩略图URL

        Args:
            obj: Formula 对象

        Returns:
            完整的缩略图URL或空字符串
        """
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.thumbnail)


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
        - author: 作者信息（动态生成）
        - created_at: 创建时间
    """
    category = CubeCategorySerializer(read_only=True)
    target_state = CubeStateSerializer(read_only=True)
    tags = FormulaTagSerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()

    class Meta:
        model = Formula
        fields = (
            'id', 'name', 'notation', 'inverse_notation', 'category', 'target_state',
            'difficulty', 'thumbnail', 'is_custom', 'tags', 'view_count', 'author', 'created_at'
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

    def get_author(self, obj):
        """
        获取作者信息

        返回作者的ID和用户名，便于前端按作者筛选。
        对于数据库初始插入的公式（created_by 为 None），返回"官方"作为作者。

        Args:
            obj: Formula 对象

        Returns:
            作者信息字典（包含 id 和 username）
        """
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username
            }
        return {'id': 0, 'username': '官方'}


class FormulaSerializer(serializers.ModelSerializer):
    """
    公式详情序列化器

    用于公式详情展示，包含完整信息和动态字段。

    设计特点：
        - 包含完整的状态定义
        - 动态计算前置状态（pre_state）
        - 支持 tag_ids 字段批量关联标签
        - 自动识别用户创建的自定义公式
        - 包含作者信息（author）

    动态字段：
        - pre_state: 前置状态定义（从目标状态推导或直接返回）
        - thumbnail: 缩略图URL（动态生成）
        - author: 作者信息（动态生成）
        - category: 分类信息（只读，展示用）
        - category_id: 分类ID（只写，创建/更新用）

    只读字段：
        - inverse_notation: 逆公式（自动生成）
        - created_at: 创建时间
        - is_custom: 是否自定义
        - view_count: 浏览次数
    """
    category = CubeCategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False)
    target_state = CubeStateSerializer(read_only=True)
    tags = FormulaTagSerializer(many=True, read_only=True)
    pre_state = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    thumbnail_file = serializers.FileField(write_only=True, required=False)
    thumbnail_path = serializers.CharField(write_only=True, required=False)
    author = serializers.SerializerMethodField()
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
            'id', 'name', 'notation', 'inverse_notation', 'category', 'category_id',
            'target_state', 'pre_state_definition', 'pre_state', 'thumbnail',
            'thumbnail_file', 'thumbnail_path',
            'difficulty', 'description', 'is_custom', 'tags', 'tag_ids',
            'view_count', 'author', 'created_at'
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

    def get_author(self, obj):
        """
        获取作者信息

        返回作者的ID和用户名，便于前端按作者筛选和显示。
        对于数据库初始插入的公式（created_by 为 None），返回"官方"作为作者。

        Args:
            obj: Formula 对象

        Returns:
            作者信息字典（包含 id 和 username）
        """
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username
            }
        return {'id': 0, 'username': '官方'}

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

        缩略图处理逻辑：
            - 如果是文件对象，进行压缩处理后保存
            - 如果是字符串（URL），直接使用该URL（从公式库选择的情况）

        自动识别逻辑：
            - 如果当前用户已登录且不是管理员，标记为自定义公式
            - 设置 created_by 为当前用户

        Args:
            validated_data: 验证后的表单数据

        Returns:
            创建的 Formula 对象
        """
        tag_ids = validated_data.pop('tag_ids', [])
        thumbnail_file = validated_data.pop('thumbnail_file', None)
        thumbnail_path = validated_data.pop('thumbnail_path', None)
        category_id = validated_data.pop('category_id', None)
        request = self.context.get('request')

        # 自动识别自定义公式
        if request and request.user.is_authenticated and not request.user.is_staff:
            validated_data['is_custom'] = True
            validated_data['created_by'] = request.user

        # 处理分类关联
        if category_id:
            try:
                category = CubeCategory.objects.get(id=category_id)
                validated_data['category'] = category
            except CubeCategory.DoesNotExist:
                pass

        if thumbnail_file:
            processed_file = process_image(
                thumbnail_file,
                max_width=512,
                max_height=512,
                quality=85,
                crop_square=True,
                convert_webp=True
            )

            new_name = f"{os.path.splitext(thumbnail_file.name)[0]}_thumbnail.webp"
            processed_image = InMemoryUploadedFile(
                processed_file,
                None,
                new_name,
                'image/webp',
                processed_file.tell(),
                None
            )

            validated_data['thumbnail'] = processed_image
        elif thumbnail_path:
            relative_path = thumbnail_path
            if '/media/' in thumbnail_path:
                relative_path = thumbnail_path.split('/media/')[1]
            validated_data['_thumbnail_path'] = relative_path

        if not thumbnail_file and not thumbnail_path:
            formula_name = validated_data.get('name', '')
            formula_notation = validated_data.get('notation', '')
            if formula_name or formula_notation:
                from cube_api.utils.image_processor import generate_formula_thumbnail
                buffer = generate_formula_thumbnail(formula_name, formula_notation)
                new_name = f"auto_formula_{uuid.uuid4().hex}.webp"
                processed_image = InMemoryUploadedFile(
                    buffer,
                    None,
                    new_name,
                    'image/webp',
                    buffer.tell(),
                    None
                )
                validated_data['thumbnail'] = processed_image

        formula = super().create(validated_data)

        # 如果是引用其他图片路径，需要重新设置
        if thumbnail_path:
            if '/media/' in thumbnail_path:
                relative_path = thumbnail_path.split('/media/')[1]
            else:
                relative_path = thumbnail_path
            formula.thumbnail.name = relative_path
            formula.save()

        # 根据分类自动关联状态（如果分类存在且公式没有关联状态）
        if formula.category and not formula.target_state:
            # 查找该分类下的第一个状态
            default_state = CubeState.objects.filter(category=formula.category).first()
            if default_state:
                formula.target_state = default_state
                formula.save()

        # 处理标签关联
        if tag_ids:
            tags = FormulaTag.objects.filter(id__in=tag_ids)
            for tag in tags:
                FormulaTagRelation.objects.get_or_create(formula=formula, tag=tag)

        return formula

    def update(self, instance, validated_data):
        """
        更新公式

        支持标签更新、缩略图上传和分类更新。

        缩略图处理逻辑：
            - 如果是文件对象，进行压缩处理后保存
            - 如果是字符串（URL），直接使用该URL（从公式库选择的情况）
            - 如果为空，保留原有图片

        Args:
            instance: 原 Formula 对象
            validated_data: 更新的数据

        Returns:
            更新后的 Formula 对象
        """
        tag_ids = validated_data.pop('tag_ids', None)
        thumbnail_file = validated_data.pop('thumbnail_file', None)
        thumbnail_path = validated_data.pop('thumbnail_path', None)
        category_id = validated_data.pop('category_id', None)
        request = self.context.get('request')

        if thumbnail_file:
            processed_file = process_image(
                thumbnail_file,
                max_width=512,
                max_height=512,
                quality=85,
                crop_square=True,
                convert_webp=True
            )

            new_name = f"{os.path.splitext(thumbnail_file.name)[0]}_thumbnail.webp"
            processed_image = InMemoryUploadedFile(
                processed_file,
                None,
                new_name,
                'image/webp',
                processed_file.tell(),
                None
            )

            validated_data['thumbnail'] = processed_image
        elif thumbnail_path:
            relative_path = thumbnail_path
            if '/media/' in thumbnail_path:
                relative_path = thumbnail_path.split('/media/')[1]
            validated_data['_thumbnail_path'] = relative_path

        if not thumbnail_file and not thumbnail_path and not instance.thumbnail:
            formula_name = validated_data.get('name', instance.name)
            formula_notation = validated_data.get('notation', instance.notation)
            if formula_name or formula_notation:
                from cube_api.utils.image_processor import generate_formula_thumbnail
                buffer = generate_formula_thumbnail(formula_name, formula_notation)
                new_name = f"auto_formula_{uuid.uuid4().hex}.webp"
                processed_image = InMemoryUploadedFile(
                    buffer,
                    None,
                    new_name,
                    'image/webp',
                    buffer.tell(),
                    None
                )
                validated_data['thumbnail'] = processed_image

        if category_id:
            try:
                category = CubeCategory.objects.get(id=category_id)
                validated_data['category'] = category
            except CubeCategory.DoesNotExist:
                pass

        # 当公式记号被修改时，重新生成逆公式
        if 'notation' in validated_data:
            from .services import FormulaService
            validated_data['inverse_notation'] = FormulaService.generate_inverse_notation(validated_data['notation'])

        formula = super().update(instance, validated_data)

        # 如果是引用其他图片路径，需要重新设置
        if thumbnail_path:
            if '/media/' in thumbnail_path:
                relative_path = thumbnail_path.split('/media/')[1]
            else:
                relative_path = thumbnail_path
            formula.thumbnail.name = relative_path
            formula.save()

        # 根据分类更新目标状态
        if category_id:
            try:
                category = CubeCategory.objects.get(id=category_id)
                if formula.target_state and formula.target_state.category != category:
                    formula.target_state = None
                if not formula.target_state:
                    default_state = CubeState.objects.filter(category=category).first()
                    if default_state:
                        formula.target_state = default_state
                        formula.save()
            except CubeCategory.DoesNotExist:
                pass

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