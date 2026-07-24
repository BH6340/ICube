# -*- coding: utf-8 -*-
"""
论坛模型层

该模块定义了论坛的核心数据模型，包括帖子、评论、标签、点赞、收藏和举报等。

设计特点：
    - **软删除设计**：帖子和评论使用状态字段标记删除，而非物理删除
    - **评论树形结构**：通过 self-referential 的 parent 字段实现多级评论
    - **中间表设计**：PostTag 自定义中间表，支持额外字段扩展
    - **统计字段冗余**：like_count、view_count 等字段冗余存储，避免频繁聚合查询
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator

User = get_user_model()


class Tag(models.Model):
    """
    标签模型

    用于对帖子进行分类，支持自定义颜色和使用次数统计。

    字段设计：
        - name: 标签名，唯一且建立索引，加速搜索
        - color: 标签颜色，用于前端展示
        - use_count: 使用次数，冗余存储避免每次查询都统计
    """
    name = models.CharField('标签名', max_length=30, unique=True, db_index=True)
    color = models.CharField('颜色', max_length=7, default='#1890ff', help_text='十六进制颜色码')
    use_count = models.IntegerField('使用次数', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_tag'
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['-use_count']

    def __str__(self):
        return self.name

    def increment_use_count(self):
        """
        增加使用次数

        使用 update_fields 参数只更新 use_count 字段，
        避免不必要的字段更新和触发器执行。
        """
        self.use_count += 1
        self.save(update_fields=['use_count'])


class PostTag(models.Model):
    """
    帖子-标签关联中间模型

    自定义中间表而非使用 Django 默认生成的中间表，原因：
        - 支持扩展额外字段（如关联时间）
        - 便于后续添加业务逻辑（如标签排序权重）
        - 提供更清晰的反向访问名（post_tags 和 tag_posts）

    约束：
        - unique_together: 同一帖子不能重复关联同一标签
    """
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='post_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='tag_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_post_tags'
        unique_together = ['post', 'tag']
        verbose_name = '帖子标签'
        verbose_name_plural = '帖子标签'


class Post(models.Model):
    """
    帖子模型

    论坛的核心数据模型，支持帖子发布、编辑、置顶、精华、软删除等功能。

    设计特点：
        - **软删除设计**：通过 status 字段标记删除，保留数据用于审计和恢复
        - **统计字段冗余**：like_count、view_count 等字段冗余存储，提高查询性能
        - **标签多对多**：通过自定义中间表 PostTag 关联标签
        - **索引优化**：建立作者-时间、状态-时间等复合索引，加速常用查询

    状态流转：
        draft → published → deleted
        published → deleted
        published → draft（撤回）
    """

    # 状态常量定义
    STATUS_CHOICES = [
        ('published', '已发布'),
        ('deleted', '已删除'),
        ('draft', '草稿'),
    ]

    # 基础信息字段
    title = models.CharField('标题', max_length=200, db_index=True, validators=[MinLengthValidator(3)])
    content = models.TextField('正文')
    # Markdown源码单独存储，支持后续编辑还原和格式转换
    content_md = models.TextField('Markdown源码', blank=True, help_text='支持上传.md文件')

    # 关联用户（作者）
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='作者'
    )

    # 统计字段（冗余存储，避免频繁聚合查询）
    view_count = models.IntegerField('浏览量', default=0)
    like_count = models.IntegerField('点赞数', default=0)
    comment_count = models.IntegerField('评论数', default=0)
    collect_count = models.IntegerField('收藏数', default=0)

    # 状态字段
    is_pinned = models.BooleanField('置顶', default=False)
    is_essence = models.BooleanField('精华', default=False)
    is_closed = models.BooleanField('关闭评论', default=False)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='published')

    # 标签（多对多关系，通过自定义中间表 PostTag）
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='posts',
        verbose_name='标签',
        through='PostTag'
    )

    # 举报功能
    report_count = models.IntegerField('举报数', default=0)

    # 时间字段
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_post'
        verbose_name = '帖子'
        verbose_name_plural = '帖子'
        # 默认排序：置顶优先 > 精华优先 > 最新发布优先
        ordering = ['-is_pinned', '-is_essence', '-created_at']
        indexes = [
            # 作者时间索引：按作者查询帖子列表
            models.Index(fields=['author', '-created_at']),
            # 创建时间索引：按时间排序查询
            models.Index(fields=['-created_at']),
            # 状态时间索引：按状态过滤查询
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def soft_delete(self):
        """
        软删除帖子

        将状态标记为 'deleted'，而非物理删除。
        这样做的好处：
            - 保留数据用于审计
            - 支持帖子恢复
            - 避免级联删除评论等关联数据
        """
        self.status = 'deleted'
        self.save(update_fields=['status'])


class Comment(models.Model):
    """
    评论模型

    支持多级评论（回复评论），通过自引用的 parent 字段实现树形结构。

    设计特点：
        - **树形结构**：通过 parent 字段指向父评论，实现多级回复
        - **软删除设计**：is_deleted 标记删除，保留数据
        - **隐藏机制**：is_hidden 支持管理员隐藏被举报评论
        - **点赞/点踩**：独立的 like_count 和 dislike_count

    查询优化策略：
        - 列表查询时只获取一级评论（parent=None）
        - 子评论通过递归或预加载获取
    """

    # 关联帖子
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='所属帖子'
    )
    # 评论作者
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='评论者'
    )
    # 父评论（自引用，实现树形结构）
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='父评论'
    )
    content = models.TextField('内容', max_length=1000, validators=[MinLengthValidator(1)])

    # 统计字段
    like_count = models.IntegerField('点赞数', default=0)
    dislike_count = models.IntegerField('点踩数', default=0)

    # 状态字段
    is_deleted = models.BooleanField('是否删除', default=False)
    is_hidden = models.BooleanField('是否隐藏（被举报）', default=False)

    # 时间字段
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_comment'
        verbose_name = '评论'
        verbose_name_plural = '评论'
        # 按创建时间升序排列，保持评论顺序
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} 评论 {self.post.title[:20]}'

    def soft_delete(self):
        """
        软删除评论

        将 is_deleted 标记为 True，而非物理删除。
        保留数据用于审计，避免级联影响。
        """
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])


class PostLike(models.Model):
    """
    帖子点赞记录模型

    记录用户对帖子的点赞操作，支持幂等性（同一用户对同一帖子只能点赞一次）。

    设计原因：
        - 独立的点赞记录表，避免在帖子表中频繁更新 like_count
        - 通过 unique_together 保证幂等性
        - 支持后续扩展（如点赞时间、取消点赞等）

    关联关系：
        - post: 关联的帖子
        - user: 点赞的用户
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_post_like'
        unique_together = ['post', 'user']
        verbose_name = '帖子点赞'
        verbose_name_plural = '帖子点赞'


class CommentLike(models.Model):
    """
    评论点赞记录模型

    支持点赞和点踩两种操作，通过 is_like 字段区分。

    设计原因：
        - 支持点赞/点踩两种交互
        - 通过 unique_together 保证幂等性
        - 与 Comment 的 like_count/dislike_count 字段同步更新

    is_like 字段含义：
        - True: 点赞
        - False: 点踩
    """
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    is_like = models.BooleanField('是否点赞', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_comment_like'
        unique_together = ['comment', 'user']
        verbose_name = '评论点赞'
        verbose_name_plural = '评论点赞'


class PostCollect(models.Model):
    """
    帖子收藏记录模型

    记录用户收藏帖子的操作，支持幂等性。

    设计原因：
        - 独立的收藏记录表，便于查询用户收藏列表
        - 通过 unique_together 保证幂等性
        - 与 Post 的 collect_count 字段同步更新
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='collects')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collects')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_post_collect'
        unique_together = ['post', 'user']
        verbose_name = '帖子收藏'
        verbose_name_plural = '帖子收藏'


class Report(models.Model):
    """
    举报记录模型

    支持用户举报帖子和评论，包含举报原因、状态流转和处理记录。

    设计特点：
        - **通用设计**：通过 content_type 和 object_id 支持帖子和评论的举报
        - **状态流转**：pending → approved/rejected
        - **幂等性**：同一用户对同一内容只能举报一次

    举报原因：
        - spam: 垃圾广告
        - violence: 暴力内容
        - harassment: 人身攻击
        - illegal: 违法违规
        - other: 其他

    处理状态：
        - pending: 待处理
        - approved: 已处理（确认违规）
        - rejected: 已驳回（不违规）
    """

    REASON_CHOICES = [
        ('spam', '垃圾广告'),
        ('violence', '暴力内容'),
        ('harassment', '人身攻击'),
        ('illegal', '违法违规'),
        ('other', '其他'),
    ]

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('approved', '已处理'),
        ('rejected', '已驳回'),
    ]

    content_type = models.CharField('内容类型', max_length=20, choices=[('post', '帖子'), ('comment', '评论')])
    object_id = models.IntegerField('内容ID')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports', verbose_name='举报人')
    reason = models.CharField('举报原因', max_length=20, choices=REASON_CHOICES)
    description = models.TextField('详细描述', blank=True)
    status = models.CharField('处理状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    handled_at = models.DateTimeField('处理时间', null=True, blank=True)
    # 处理人使用 SET_NULL，避免删除管理员账号导致数据丢失
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_reports')

    class Meta:
        app_label = 'forum'
        db_table = 'forum_report'
        verbose_name = '举报'
        verbose_name_plural = '举报'
        # 同一用户对同一内容只能举报一次
        unique_together = ['content_type', 'object_id', 'reporter']


class PostImage(models.Model):
    """
    帖子图片模型

    存储帖子中的图片，支持排序和图片描述。

    设计特点：
        - **延迟关联**：post 字段允许为空，支持图片先上传后关联帖子
        - **排序支持**：order 字段控制图片展示顺序
        - **描述字段**：alt 字段用于 SEO 和无障碍访问

    上传路径：
        - forum/posts/%Y/%m/：按年月分目录存储，避免单目录文件过多
    """
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='所属帖子',
        null=True,
        blank=True  # 允许为空，支持先上传图片后关联帖子
    )
    image = models.ImageField(
        upload_to='forum/posts/%Y/%m/',
        verbose_name='图片'
    )
    alt = models.CharField('图片描述', max_length=200, blank=True)
    order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_post_image'
        verbose_name = '帖子图片'
        verbose_name_plural = '帖子图片'
        # 按排序字段和创建时间排序
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.post.title} - {self.id}'
