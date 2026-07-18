# forum/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator

User = get_user_model()


class Tag(models.Model):
    """标签模型"""
    name = models.CharField('标签名', max_length=30, unique=True, db_index=True)
    color = models.CharField('颜色', max_length=7, default='#1890ff', help_text='十六进制颜色码')
    use_count = models.IntegerField('使用次数', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'  # ✅ 添加这一行
        db_table = 'forum_tag'
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['-use_count']

    def __str__(self):
        return self.name

    def increment_use_count(self):
        """增加使用次数"""
        self.use_count += 1
        self.save(update_fields=['use_count'])


# ✅ 再定义 PostTag 中间模型
class PostTag(models.Model):
    """帖子-标签关联表"""
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
    """帖子模型"""

    # 状态常量
    STATUS_CHOICES = [
        ('published', '已发布'),
        ('deleted', '已删除'),
        ('draft', '草稿'),
    ]

    # 基础信息
    title = models.CharField('标题', max_length=200, db_index=True, validators=[MinLengthValidator(3)])
    content = models.TextField('正文')
    content_md = models.TextField('Markdown源码', blank=True, help_text='支持上传.md文件')

    # 关联用户
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='作者'
    )

    # 统计字段
    view_count = models.IntegerField('浏览量', default=0)
    like_count = models.IntegerField('点赞数', default=0)
    comment_count = models.IntegerField('评论数', default=0)
    collect_count = models.IntegerField('收藏数', default=0)

    # 状态字段
    is_pinned = models.BooleanField('置顶', default=False)
    is_essence = models.BooleanField('精华', default=False)
    is_closed = models.BooleanField('关闭评论', default=False)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='published')

    # 标签（多对多）
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='posts',
        verbose_name='标签',
        through='PostTag'  # 指定中间表
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
        ordering = ['-is_pinned', '-is_essence', '-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return self.title

    def soft_delete(self):
        """软删除"""
        self.status = 'deleted'
        self.save(update_fields=['status'])


class Comment(models.Model):
    """评论模型"""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='所属帖子'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='评论者'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='父评论'
    )
    content = models.TextField('内容', max_length=1000, validators=[MinLengthValidator(1)])

    # 统计
    like_count = models.IntegerField('点赞数', default=0)
    dislike_count = models.IntegerField('点踩数', default=0)

    # 状态
    is_deleted = models.BooleanField('是否删除', default=False)
    is_hidden = models.BooleanField('是否隐藏（被举报）', default=False)

    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_comment'
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.author} 评论 {self.post.title[:20]}'

    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])


class PostLike(models.Model):
    """帖子点赞记录"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_post_like'
        unique_together = ['post', 'user']


class CommentLike(models.Model):
    """评论点赞记录"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes')
    is_like = models.BooleanField('是否点赞', default=True)  # True:点赞, False:点踩
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_comment_like'
        unique_together = ['comment', 'user']


class PostCollect(models.Model):
    """帖子收藏记录"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='collects')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collects')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'forum'
        db_table = 'forum_post_collect'
        unique_together = ['post', 'user']


class Report(models.Model):
    """举报记录"""

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
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_reports')

    class Meta:
        app_label = 'forum'
        db_table = 'forum_report'
        verbose_name = '举报'
        verbose_name_plural = '举报'
        unique_together = ['content_type', 'object_id', 'reporter']  # 同一用户对同一内容只能举报一次
