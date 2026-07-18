from django.contrib import admin

from .models import CubeCategory, CubeState, Formula, FormulaTag, FormulaTagRelation, FormulaCollection


@admin.register(CubeCategory)
class CubeCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'order', 'method', 'phase', 'sort_order', 'created_at')
    list_filter = ('order', 'method', 'phase')
    search_fields = ('name', 'method', 'phase')
    ordering = ('order', 'method', 'sort_order')


@admin.register(CubeState)
class CubeStateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('name',)


@admin.register(Formula)
class FormulaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'difficulty', 'is_custom', 'created_by', 'created_at')
    list_filter = ('category', 'difficulty', 'is_custom')
    search_fields = ('name', 'notation')
    raw_id_fields = ('target_state', 'created_by')


@admin.register(FormulaTag)
class FormulaTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'created_at')
    search_fields = ('name',)


@admin.register(FormulaTagRelation)
class FormulaTagRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'formula', 'tag')
    list_filter = ('formula', 'tag')


@admin.register(FormulaCollection)
class FormulaCollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'formula', 'created_at')
    list_filter = ('user',)