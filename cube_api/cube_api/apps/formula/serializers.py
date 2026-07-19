from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.conf import settings
from django.core.files.storage import default_storage

from .models import CubeCategory, CubeState, Formula, FormulaTag, FormulaTagRelation, FormulaCollection
from .services import CubeStateService


class CubeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CubeCategory
        fields = ('id', 'order', 'method', 'phase', 'name', 'description', 'sort_order', 'created_at')


class CubeStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CubeState
        fields = ('id', 'name', 'state_definition', 'description', 'category', 'created_at')
        read_only_fields = ('created_at',)

    def validate_state_definition(self, value):
        errors = CubeStateService.validate_state_definition(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value


class FormulaTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormulaTag
        fields = ('id', 'name', 'color', 'created_at')
        read_only_fields = ('created_at',)


class FormulaListSerializer(serializers.ModelSerializer):
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
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.thumbnail)


class FormulaSerializer(serializers.ModelSerializer):
    category = CubeCategorySerializer(read_only=True)
    target_state = CubeStateSerializer(read_only=True)
    tags = FormulaTagSerializer(many=True, read_only=True)
    pre_state = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
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
        return obj.get_pre_state()

    def get_thumbnail(self, obj):
        from cube_api.utils.image_url import build_image_url
        return build_image_url(obj.thumbnail)

    def validate_pre_state_definition(self, value):
        if value:
            errors = CubeStateService.validate_state_definition(value)
            if errors:
                raise serializers.ValidationError(errors)
        return value

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        thumbnail_file = validated_data.pop('thumbnail', None)
        request = self.context.get('request')

        if request and request.user.is_authenticated and not request.user.is_staff:
            validated_data['is_custom'] = True
            validated_data['created_by'] = request.user

        if thumbnail_file:
            saved_path = default_storage.save(f"formula_thumbnails/{thumbnail_file.name}", thumbnail_file)
            validated_data['thumbnail'] = f"{settings.MEDIA_URL}{saved_path}"

        formula = super().create(validated_data)

        if tag_ids:
            tags = FormulaTag.objects.filter(id__in=tag_ids)
            for tag in tags:
                FormulaTagRelation.objects.get_or_create(formula=formula, tag=tag)

        return formula

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        thumbnail_file = validated_data.pop('thumbnail', None)
        request = self.context.get('request')

        if thumbnail_file:
            saved_path = default_storage.save(f"formula_thumbnails/{thumbnail_file.name}", thumbnail_file)
            validated_data['thumbnail'] = f"{settings.MEDIA_URL}{saved_path}"

        formula = super().update(instance, validated_data)

        if tag_ids is not None:
            FormulaTagRelation.objects.filter(formula=formula).delete()
            tags = FormulaTag.objects.filter(id__in=tag_ids)
            for tag in tags:
                FormulaTagRelation.objects.get_or_create(formula=formula, tag=tag)

        return formula


class FormulaMatchSerializer(serializers.Serializer):
    state_definition = serializers.JSONField(help_text='用户当前魔方状态')

    def validate_state_definition(self, value):
        errors = CubeStateService.validate_state_definition(value)
        if errors:
            raise serializers.ValidationError(errors)
        return value


class FormulaCollectionSerializer(serializers.ModelSerializer):
    formula = FormulaListSerializer(read_only=True)

    class Meta:
        model = FormulaCollection
        fields = ('id', 'formula', 'created_at')
        read_only_fields = ('created_at',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)