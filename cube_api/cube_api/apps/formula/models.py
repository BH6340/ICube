from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class CubeCategory(models.Model):
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
        if self.notation and not self.inverse_notation:
            from .services import FormulaService
            self.inverse_notation = FormulaService.generate_inverse_notation(self.notation)

        super().save(*args, **kwargs)

    def get_pre_state(self):
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
    name = models.CharField('标签名称', max_length=50, unique=True)
    color = models.CharField('标签颜色', max_length=7, default='#1890ff')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'formula'
        db_table = 'formula_formula_tag'

    def __str__(self):
        return self.name


class FormulaTagRelation(models.Model):
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='formula_collections')
    formula = models.ForeignKey('Formula', on_delete=models.CASCADE, related_name='collections')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'formula'
        db_table = 'formula_formula_collection'
        unique_together = ['user', 'formula']