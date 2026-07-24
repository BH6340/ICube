# -*- coding: utf-8 -*-
"""
论坛后台管理模块

该模块基于 django-unfold 为论坛应用提供现代化的后台管理界面。

设计要点：
    - 所有 Admin 类继承 unfold.admin.ModelAdmin，获得 Unfold 的现代 UI 风格
    - 使用 @display 装饰器自定义展示字段（Badge、缩略图等）
    - 使用 @action 装饰器定义批量操作
    - 统计字段设置为只读，避免人工误改系统维护的数据
    - 关联字段使用 raw_id_fields，避免下拉框加载大量数据导致页面卡顿
"""
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils import timezone

from unfold.admin import ModelAdmin
from unfold.decorators import display, action

from .models import (
    Tag,
    PostTag,
    Post,
    Comment,
    PostLike,
    CommentLike,
    PostCollect,
    Report,
    PostImage,
)


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    """
    标签后台管理

    提供标签列表展示、搜索功能，并通过颜色徽章直观展示标签颜色。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示标签的核心信息，颜色徽章帮助管理员直观识别标签
    list_display = ('name', 'color_badge', 'use_count', 'created_at')

    # search_fields: 搜索字段配置
    # 配置原因：标签名是唯一的，按名称搜索最高效
    search_fields = ('name',)

    # use_count 为系统维护字段，不可在列表中编辑，故不加入 list_editable
    # 配置原因：use_count 由系统通过 increment_use_count 维护，人工编辑会导致数据不一致

    @display(description='颜色')
    def color_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段
        作用：渲染带颜色背景的 span 标签，直观展示标签颜色
        """
        return mark_safe(
            f'<span style="background:{obj.color}; color:#fff; '
            f'padding:2px 10px; border-radius:4px;">{obj.color}</span>'
        )


@admin.register(PostTag)
class PostTagAdmin(ModelAdmin):
    """
    帖子-标签关联后台管理

    管理帖子与标签的多对多关联记录。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示关联关系的基础信息，便于快速定位关联记录
    list_display = ('post', 'tag', 'created_at')

    # raw_id_fields: 原始 ID 选择器配置
    # 配置原因：帖子和标签数据量可能很大，使用下拉框会加载全部数据导致页面卡顿
    raw_id_fields = ('post', 'tag')


@admin.register(Post)
class PostAdmin(ModelAdmin):
    """
    帖子后台管理（核心）

    提供帖子的完整管理功能，包括状态徽章展示、统计字段只读保护、
    以及批量置顶、加精、软删除等运维操作。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示帖子标题、作者、状态徽章、置顶/精华标记及核心统计数据
    list_display = (
        'title',
        'author',
        'status_badge',
        'is_pinned_badge',
        'is_essence_badge',
        'view_count',
        'like_count',
        'created_at',
    )

    # search_fields: 搜索字段配置
    # 配置原因：管理员常按标题或正文内容检索帖子
    search_fields = ('title', 'content')

    # list_filter: 侧边过滤字段配置
    # 配置原因：按状态、置顶、精华、创建时间快速筛选帖子
    list_filter = ('status', 'is_pinned', 'is_essence', 'created_at')

    # fieldsets: 编辑页字段分组配置
    # 配置原因：将字段按业务语义分组，提升编辑体验和可读性
    fieldsets = (
        ('基础信息', {
            'fields': ('title', 'content', 'content_md', 'author'),
        }),
        ('统计数据', {
            'fields': ('view_count', 'like_count', 'comment_count', 'collect_count'),
        }),
        ('状态控制', {
            'fields': ('status', 'is_pinned', 'is_essence', 'is_closed'),
        }),
    )

    # readonly_fields: 只读字段配置
    # 配置原因：统计字段由系统自动维护（如点赞时更新 like_count），
    # 人工编辑会导致与明细表数据不一致，故设为只读
    readonly_fields = ('view_count', 'like_count', 'comment_count', 'collect_count', 'report_count')

    # raw_id_fields: 原始 ID 选择器配置
    # 配置原因：作者（User）数据量可能很大，使用下拉框会加载全部用户导致页面卡顿
    raw_id_fields = ('author',)

    # actions: 批量操作配置
    # 配置原因：管理员需要对帖子进行批量置顶、加精、软删除等运维操作
    actions = ('batch_pin', 'batch_unpin', 'batch_essence', 'batch_soft_delete')

    @display(description='状态', ordering='status')
    def status_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段
        作用：根据帖子状态渲染不同颜色的 Badge，便于管理员快速识别帖子状态
        """
        status_map = {
            'published': ('已发布', 'bg-green-100 text-green-800'),
            'deleted': ('已删除', 'bg-red-100 text-red-800'),
            'draft': ('草稿', 'bg-gray-100 text-gray-800'),
        }
        text, css_class = status_map.get(obj.status, (obj.status, 'bg-gray-100 text-gray-800'))
        return mark_safe(
            f'<span class="{css_class}" style="padding:2px 10px; border-radius:4px;">{text}</span>'
        )

    @display(description='置顶', boolean=True, ordering='is_pinned')
    def is_pinned_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段，boolean=True 渲染为图标
        作用：用对勾/叉号直观标识帖子是否置顶
        """
        return obj.is_pinned

    @display(description='精华', boolean=True, ordering='is_essence')
    def is_essence_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段，boolean=True 渲染为图标
        作用：用对勾/叉号直观标识帖子是否为精华
        """
        return obj.is_essence

    @action(description='批量置顶', url_path='batch-pin')
    def batch_pin(self, request, queryset):
        """
        @action 装饰器：将方法注册为批量操作
        作用：将选中的帖子批量设置为置顶状态
        """
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'成功置顶 {updated} 篇帖子')

    @action(description='取消置顶', url_path='batch-unpin')
    def batch_unpin(self, request, queryset):
        """
        @action 装饰器：将方法注册为批量操作
        作用：将选中的帖子批量取消置顶
        """
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'成功取消置顶 {updated} 篇帖子')

    @action(description='批量加精', url_path='batch-essence')
    def batch_essence(self, request, queryset):
        """
        @action 装饰器：将方法注册为批量操作
        作用：将选中的帖子批量设置为精华帖
        """
        updated = queryset.update(is_essence=True)
        self.message_user(request, f'成功加精 {updated} 篇帖子')

    @action(description='批量软删除', url_path='batch-soft-delete')
    def batch_soft_delete(self, request, queryset):
        """
        @action 装饰器：将方法注册为批量操作
        作用：将选中的帖子状态设置为 deleted（软删除），保留数据用于审计和恢复
        """
        updated = queryset.update(status='deleted')
        self.message_user(request, f'成功软删除 {updated} 篇帖子')


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    """
    评论后台管理

    提供评论列表展示（内容截断）、状态徽章及批量隐藏/恢复操作。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示评论所属帖子、作者、截断内容、点赞/点踩数及状态徽章
    list_display = (
        'post',
        'author',
        'content_truncated',
        'like_count',
        'dislike_count',
        'is_deleted_badge',
        'is_hidden_badge',
        'created_at',
    )

    # search_fields: 搜索字段配置
    # 配置原因：管理员按评论内容检索评论
    search_fields = ('content',)

    # list_filter: 侧边过滤字段配置
    # 配置原因：按删除、隐藏状态及创建时间快速筛选评论
    list_filter = ('is_deleted', 'is_hidden', 'created_at')

    # raw_id_fields: 原始 ID 选择器配置
    # 配置原因：帖子、用户、父评论数据量可能很大，使用下拉框会加载过多数据
    raw_id_fields = ('post', 'author', 'parent')

    # actions: 批量操作配置
    # 配置原因：管理员需要批量隐藏违规评论或恢复显示
    actions = ('batch_hide', 'batch_show')

    @display(description='内容')
    def content_truncated(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段
        作用：截断评论内容前 30 个字符，避免长评论撑爆列表行高
        """
        text = obj.content[:30]
        if len(obj.content) > 30:
            text += '...'
        return text

    @display(description='已删除', boolean=True, ordering='is_deleted')
    def is_deleted_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段，boolean=True 渲染为图标
        作用：用对勾/叉号直观标识评论是否已被软删除
        """
        return obj.is_deleted

    @display(description='已隐藏', boolean=True, ordering='is_hidden')
    def is_hidden_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段，boolean=True 渲染为图标
        作用：用对勾/叉号直观标识评论是否已被管理员隐藏
        """
        return obj.is_hidden

    @action(description='批量隐藏', url_path='batch-hide')
    def batch_hide(self, request, queryset):
        """
        @action 装饰器：将方法注册为批量操作
        作用：将选中的评论批量设置为隐藏状态，用于处理违规评论
        """
        updated = queryset.update(is_hidden=True)
        self.message_user(request, f'成功隐藏 {updated} 条评论')

    @action(description='恢复显示', url_path='batch-show')
    def batch_show(self, request, queryset):
        """
        @action 装饰器：将方法注册为批量操作
        作用：将选中的评论批量恢复显示
        """
        updated = queryset.update(is_hidden=False)
        self.message_user(request, f'成功恢复 {updated} 条评论')


@admin.register(PostLike)
class PostLikeAdmin(ModelAdmin):
    """
    帖子点赞记录后台管理

    提供点赞记录的列表展示与按时间过滤。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示点赞关联的帖子、用户及点赞时间
    list_display = ('post', 'user', 'created_at')

    # list_filter: 侧边过滤字段配置
    # 配置原因：按创建时间筛选点赞记录，便于按时间段统计
    list_filter = ('created_at',)

    # raw_id_fields: 原始 ID 选择器配置
    # 配置原因：帖子和用户数据量可能很大，使用下拉框会加载过多数据
    raw_id_fields = ('post', 'user')


@admin.register(CommentLike)
class CommentLikeAdmin(ModelAdmin):
    """
    评论点赞记录后台管理

    提供点赞/点踩记录的列表展示，通过 Badge 区分点赞与点踩。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示点赞关联的评论、用户、类型徽章及时间
    list_display = ('comment', 'user', 'is_like_badge', 'created_at')

    # list_filter: 侧边过滤字段配置
    # 配置原因：按是否点赞和创建时间筛选，便于分析点赞/点踩分布
    list_filter = ('is_like', 'created_at')

    # raw_id_fields: 原始 ID 选择器配置
    # 配置原因：评论和用户数据量可能很大，使用下拉框会加载过多数据
    raw_id_fields = ('comment', 'user')

    @display(description='类型', boolean=True, ordering='is_like')
    def is_like_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段，boolean=True 渲染为图标
        作用：用对勾/叉号直观标识是点赞（True）还是点踩（False）
        """
        return obj.is_like


@admin.register(PostCollect)
class PostCollectAdmin(ModelAdmin):
    """
    帖子收藏记录后台管理

    提供收藏记录的列表展示与按时间过滤。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示收藏关联的帖子、用户及收藏时间
    list_display = ('post', 'user', 'created_at')

    # list_filter: 侧边过滤字段配置
    # 配置原因：按创建时间筛选收藏记录，便于按时间段统计
    list_filter = ('created_at',)

    # raw_id_fields: 原始 ID 选择器配置
    # 配置原因：帖子和用户数据量可能很大，使用下拉框会加载过多数据
    raw_id_fields = ('post', 'user')


@admin.register(Report)
class ReportAdmin(ModelAdmin):
    """
    举报后台管理（核心）

    提供举报记录的完整管理流程，包括内容类型、原因、状态的 Badge 展示，
    以及批量审批、驳回等处理操作。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示举报的核心信息，通过 Badge 直观呈现内容类型、原因和处理状态
    list_display = (
        'content_type_badge',
        'object_id',
        'reporter',
        'reason_badge',
        'status_badge',
        'created_at',
        'handler',
    )

    # search_fields: 搜索字段配置
    # 配置原因：管理员按举报详细描述检索举报记录
    search_fields = ('description',)

    # list_filter: 侧边过滤字段配置
    # 配置原因：按内容类型、原因、状态、创建时间快速筛选举报记录
    list_filter = ('content_type', 'reason', 'status', 'created_at')

    # readonly_fields: 只读字段配置
    # 配置原因：创建时间、处理时间由系统维护，举报人信息不可篡改以保证审计可信
    readonly_fields = ('created_at', 'handled_at', 'reporter')

    # raw_id_fields: 原始 ID 选择器配置
    # 配置原因：举报人和处理人（User）数据量可能很大，使用下拉框会加载过多数据
    raw_id_fields = ('reporter', 'handler')

    # actions: 批量操作配置
    # 配置原因：管理员需要批量处理或驳回举报记录
    actions = ('batch_approve', 'batch_reject')

    @display(description='内容类型', ordering='content_type')
    def content_type_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段
        作用：根据内容类型渲染不同颜色的 Badge，便于区分帖子/评论举报
        """
        type_map = {
            'post': ('帖子', 'bg-blue-100 text-blue-800'),
            'comment': ('评论', 'bg-purple-100 text-purple-800'),
        }
        text, css_class = type_map.get(obj.content_type, (obj.content_type, 'bg-gray-100 text-gray-800'))
        return mark_safe(
            f'<span class="{css_class}" style="padding:2px 10px; border-radius:4px;">{text}</span>'
        )

    @display(description='举报原因', ordering='reason')
    def reason_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段
        作用：根据举报原因渲染不同颜色的 Badge，便于快速识别严重程度
        """
        reason_map = {
            'spam': ('垃圾广告', 'bg-yellow-100 text-yellow-800'),
            'violence': ('暴力内容', 'bg-red-100 text-red-800'),
            'harassment': ('人身攻击', 'bg-orange-100 text-orange-800'),
            'illegal': ('违法违规', 'bg-red-200 text-red-900'),
            'other': ('其他', 'bg-gray-100 text-gray-800'),
        }
        text, css_class = reason_map.get(obj.reason, (obj.reason, 'bg-gray-100 text-gray-800'))
        return mark_safe(
            f'<span class="{css_class}" style="padding:2px 10px; border-radius:4px;">{text}</span>'
        )

    @display(description='处理状态', ordering='status')
    def status_badge(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段
        作用：根据处理状态渲染不同颜色的 Badge，便于跟踪举报处理进度
        """
        status_map = {
            'pending': ('待处理', 'bg-yellow-100 text-yellow-800'),
            'approved': ('已处理', 'bg-green-100 text-green-800'),
            'rejected': ('已驳回', 'bg-gray-100 text-gray-800'),
        }
        text, css_class = status_map.get(obj.status, (obj.status, 'bg-gray-100 text-gray-800'))
        return mark_safe(
            f'<span class="{css_class}" style="padding:2px 10px; border-radius:4px;">{text}</span>'
        )

    @action(description='批量处理（确认违规）', url_path='batch-approve')
    def batch_approve(self, request, queryset):
        """
        @action 装饰器：将方法注册为批量操作
        作用：将选中的举报批量标记为已处理（approved），并记录处理时间和处理人
        """
        updated = queryset.update(
            status='approved',
            handled_at=timezone.now(),
            handler=request.user,
        )
        self.message_user(request, f'成功处理 {updated} 条举报')

    @action(description='批量驳回', url_path='batch-reject')
    def batch_reject(self, request, queryset):
        """
        @action 装饰器：将方法注册为批量操作
        作用：将选中的举报批量驳回（rejected），并记录处理时间和处理人
        """
        updated = queryset.update(
            status='rejected',
            handled_at=timezone.now(),
            handler=request.user,
        )
        self.message_user(request, f'成功驳回 {updated} 条举报')


@admin.register(PostImage)
class PostImageAdmin(ModelAdmin):
    """
    帖子图片后台管理

    提供图片列表展示（含缩略图预览）及排序管理。
    """

    # list_display: 列表页展示字段配置
    # 配置原因：展示图片缩略图、所属帖子、描述、排序及创建时间
    list_display = ('image_preview', 'post', 'alt', 'order', 'created_at')

    # raw_id_fields: 原始 ID 选择器配置
    # 配置原因：帖子数据量可能很大，使用下拉框会加载过多数据
    raw_id_fields = ('post',)

    @display(description='预览图')
    def image_preview(self, obj):
        """
        @display 装饰器：将方法注册为列表展示字段
        作用：渲染图片缩略图，便于管理员直观查看图片内容
        """
        if not obj.image:
            return '无图片'
        return mark_safe(
            f'<img src="{obj.image.url}" style="max-height:60px; max-width:80px; '
            f'object-fit:cover; border-radius:4px;" />'
        )
