# -*- coding: utf-8 -*-
"""
论坛序列化器层

该模块定义了论坛相关模型的序列化器，负责数据的序列化和反序列化。

设计特点：
    - **动态字段**：使用 SerializerMethodField 处理动态计算字段（如 is_liked）
    - **多序列化器策略**：列表和详情使用不同的序列化器，减少数据传输
    - **图片URL标准化**：统一使用 build_image_url 生成完整URL
    - **标签处理**：支持 tag_ids 字段批量关联标签
"""
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import Post, Tag, Comment, PostLike, CommentLike, PostCollect, Report, PostImage
from apps.accounts.serializers import ProfileListSerializer, UserSerializer


class TagSerializer(serializers.ModelSerializer):
    """
    标签序列化器

    序列化标签数据，包含基本信息和使用次数。

    字段：
        - id: 标签ID
        - name: 标签名
        - color: 标签颜色
        - use_count: 使用次数
    """

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'use_count')


class PostImageSerializer(serializers.ModelSerializer):
    """
    帖子图片序列化器

    序列化帖子图片数据，自动生成完整的图片URL。

    字段：
        - id: 图片ID
        - image: 图片文件（只读）
        - image_url: 完整图片URL（动态生成）
        - alt: 图片描述
        - order: 排序
        - created_at: 创建时间
    """
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PostImage
        fields = ('id', 'image', 'image_url', 'alt', 'order', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_image_url(self, obj):
        """
        生成完整的图片URL

        使用 build_image_url 工具函数，统一处理图片URL的生成逻辑。

        Args:
            obj: PostImage 对象

        Returns:
            完整的图片URL或空字符串
        """
        from cube_api.utils.image_url import build_image_url
        if obj.image:
            return build_image_url(obj.image.url)
        return ''


class PostListSerializer(serializers.ModelSerializer):
    """
    帖子列表序列化器（轻量级）

    用于帖子列表展示，包含必要字段和图片预览。

    设计原因：
        - 列表页不需要完整内容，轻量级序列化器提高加载速度
        - 包含前4张图片预览，丰富列表展示效果
        - 减少网络带宽消耗

    字段：
        - id: 帖子ID
        - title: 标题
        - author: 作者资料（轻量级）
        - view_count/like_count/comment_count: 统计数据
        - tags: 标签列表
        - images: 图片预览（最多4张）
        - is_pinned/is_essence: 状态标记
        - created_at/updated_at: 时间
    """
    author = ProfileListSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'author', 'view_count', 'like_count',
            'comment_count', 'tags', 'images', 'is_pinned', 'is_essence',
            'created_at', 'updated_at'
        )

    def get_images(self, obj):
        """
        获取帖子的图片列表（最多4张）

        Args:
            obj: Post 对象

        Returns:
            图片序列化数据列表
        """
        images = obj.images.all()[:4]
        return PostImageSerializer(images, many=True, context=self.context).data


class PostSerializer(serializers.ModelSerializer):
    """
    帖子详情序列化器

    用于帖子详情展示，包含完整信息和动态字段。

    设计特点：
        - 包含完整内容和图片
        - 动态计算用户点赞/收藏状态
        - 支持 tag_ids 字段批量关联标签

    动态字段：
        - is_liked: 当前用户是否点赞
        - is_collected: 当前用户是否收藏
    """
    author = ProfileListSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()
    # 用于批量关联标签的写入字段
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='标签ID列表'
    )

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'content', 'content_md', 'author', 'view_count', 'like_count',
            'comment_count', 'collect_count', 'tags', 'images', 'tag_ids', 'is_pinned', 'is_essence',
            'is_closed', 'status', 'report_count', 'created_at', 'updated_at',
            'is_liked', 'is_collected'
        )
        # 统计字段和时间字段只读，由系统自动更新
        read_only_fields = ('view_count', 'like_count', 'comment_count',
                            'collect_count', 'report_count', 'status', 'created_at', 'updated_at')

    @extend_schema_field(serializers.BooleanField)
    def get_is_liked(self, obj):
        """
        判断当前用户是否点赞

        通过查询 PostLike 表判断用户是否已点赞。

        Args:
            obj: Post 对象

        Returns:
            True（已点赞）或 False（未点赞）
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user).exists()
        return False

    @extend_schema_field(serializers.BooleanField)
    def get_is_collected(self, obj):
        """
        判断当前用户是否收藏

        通过查询 PostCollect 表判断用户是否已收藏。

        Args:
            obj: Post 对象

        Returns:
            True（已收藏）或 False（未收藏）
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostCollect.objects.filter(post=obj, user=request.user).exists()
        return False

    def create(self, validated_data):
        """
        创建帖子

        处理标签关联和标签使用次数递增。

        Args:
            validated_data: 验证后的表单数据

        Returns:
            创建的 Post 对象
        """
        tag_ids = validated_data.pop('tag_ids', [])
        # 设置作者为当前用户
        validated_data['author'] = self.context['request'].user
        post = super().create(validated_data)

        # 处理标签关联
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            post.tags.set(tags)
            # 递增标签使用次数
            for tag in tags:
                tag.increment_use_count()

        return post

    def update(self, instance, validated_data):
        """
        更新帖子

        支持标签更新。

        Args:
            instance: 原 Post 对象
            validated_data: 更新的数据

        Returns:
            更新后的 Post 对象
        """
        tag_ids = validated_data.pop('tag_ids', None)
        post = super().update(instance, validated_data)

        # 更新标签关联
        if tag_ids is not None:
            post.tags.set(tag_ids)

        return post


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """
    创建/更新帖子的序列化器

    支持多种内容输入方式：
        - 直接输入 content 字段
        - 上传 .md 文件自动解析
        - 上传图片列表

    设计特点：
        - 支持文件上传（.md 文件和图片）
        - 图片先上传后关联的延迟关联机制
        - 标签批量关联

    验证规则：
        - 标题：3-200 字符
        - 内容：至少 10 字符
        - 文件：只支持 .md 格式，大小不超过 5MB
    """
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    content_file = serializers.FileField(write_only=True, required=False, help_text='上传.md文件')
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        help_text='上传图片列表'
    )

    class Meta:
        model = Post
        fields = ('id', 'title', 'content', 'content_md', 'content_file', 'tag_ids', 'tags', 'images')
        read_only_fields = ('id',)

    def validate_title(self, value):
        """
        验证标题

        Args:
            value: 标题字符串

        Raises:
            ValidationError: 标题不符合要求

        Returns:
            清洗后的标题
        """
        if len(value.strip()) < 3:
            raise serializers.ValidationError("标题至少3个字符")
        if len(value) > 200:
            raise serializers.ValidationError("标题不能超过200个字符")
        return value.strip()

    def validate_content(self, value):
        """
        验证内容

        Args:
            value: 内容字符串

        Raises:
            ValidationError: 内容不符合要求

        Returns:
            清洗后的内容
        """
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("内容至少10个字符")
        return value.strip() if value else ''

    def validate_content_file(self, value):
        """
        验证上传的.md文件

        Args:
            value: 文件对象

        Raises:
            ValidationError: 文件不符合要求

        Returns:
            验证通过的文件对象
        """
        if not value.name.endswith('.md'):
            raise serializers.ValidationError("只支持.md格式的文件")
        if value.size > 1024 * 1024 * 5:  # 5MB
            raise serializers.ValidationError("文件大小不能超过5MB")
        return value

    def create(self, validated_data):
        """
        创建帖子

        支持三种内容输入方式：
            1. 直接输入 content
            2. 上传 .md 文件自动解析
            3. 上传图片列表

        同时处理标签关联和图片关联。

        Args:
            validated_data: 验证后的表单数据

        Returns:
            创建的 Post 对象
        """
        tag_ids = validated_data.pop('tag_ids', [])
        content_file = validated_data.pop('content_file', None)
        images = validated_data.pop('images', [])

        # 处理 .md 文件上传
        if content_file:
            content = content_file.read().decode('utf-8')
            validated_data['content'] = content
            validated_data['content_md'] = content

        # 设置作者为当前用户
        validated_data['author'] = self.context['request'].user
        post = Post.objects.create(**validated_data)

        # 处理标签关联
        if tag_ids:
            post.tags.set(tag_ids)

        # 处理直接上传的图片
        for idx, image in enumerate(images):
            PostImage.objects.create(
                post=post,
                image=image,
                alt=f'图片{idx + 1}',
                order=idx
            )

        self._sync_post_images(post, validated_data.get('content', ''))

        return post

    def _sync_post_images(self, post, content):
        """
        根据帖子内容同步图片关联

        核心逻辑：
            1. 从内容中提取所有Markdown格式的图片URL
            2. 获取当前已关联的图片路径集合
            3. 删除不在内容中的图片关联（已删除的图片）
            4. 添加新出现在内容中的图片关联（新插入的图片）

        支持的图片来源：
            - 用户上传图片：/media/forum/posts/
            - 公式库缩略图：/media/formulas/

        Args:
            post: Post 对象
            content: 帖子内容（可能包含图片URL）
        """
        import re
        import os
        from django.conf import settings

        image_urls = re.findall(r'!\[.*?\]\((.*?)\)', content)

        existing_images = set()
        for img in post.images.all():
            existing_images.add(img.image.name)

        required_images = set()
        for url in image_urls:
            if '/media/forum/posts/' in url or '/media/formulas/' in url:
                image_path = url.split('/media/')[-1]
                required_images.add(image_path)

        for img in list(post.images.all()):
            if img.image.name not in required_images:
                img.delete()

        for image_path in required_images:
            if image_path not in existing_images:
                full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                if os.path.exists(full_path):
                    PostImage.objects.create(
                        post=post,
                        image=image_path,
                        alt='图片',
                        order=post.images.count()
                    )

    def update(self, instance, validated_data):
        """
        更新帖子

        支持标签更新、图片上传和文件上传。

        Args:
            instance: 原 Post 对象
            validated_data: 更新的数据

        Returns:
            更新后的 Post 对象
        """
        tag_ids = validated_data.pop('tag_ids', None)
        images = validated_data.pop('images', [])
        content_file = validated_data.pop('content_file', None)

        # 处理 .md 文件上传
        if content_file:
            content = content_file.read().decode('utf-8')
            validated_data['content'] = content
            validated_data['content_md'] = content

        post = super().update(instance, validated_data)

        # 更新标签关联
        if tag_ids is not None:
            post.tags.set(tag_ids)

        # 处理直接上传的图片
        for idx, image in enumerate(images):
            PostImage.objects.create(
                post=post,
                image=image,
                alt=f'图片{idx + 1}',
                order=idx
            )

        self._sync_post_images(post, validated_data.get('content', ''))

        return post


class ReplySerializer(serializers.ModelSerializer):
    """
    子评论序列化器

    用于序列化二级及以下的评论回复，包含动态状态字段。

    设计特点：
        - 包含被回复人的用户名（reply_to_name）
        - 包含当前用户的点赞/点踩状态
        - 轻量级设计，不含 replies 字段（避免递归）

    动态字段：
        - reply_to_name: 被回复人的用户名
        - liked: 当前用户是否点赞
        - disliked: 当前用户是否点踩
    """
    author = UserSerializer(read_only=True)
    reply_to_name = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'created_at', 'author', 'parent',
            'reply_to_name', 'like_count', 'dislike_count', 'liked', 'disliked'
        ]

    def get_reply_to_name(self, obj):
        """
        获取被回复人的用户名

        通过父评论的作者获取被回复人的用户名。

        Args:
            obj: Comment 对象

        Returns:
            被回复人的用户名或 None
        """
        if obj.parent and obj.parent.author:
            return obj.parent.author.username
        return None

    def get_liked(self, obj):
        """
        判断当前用户是否点赞

        Args:
            obj: Comment 对象

        Returns:
            True（已点赞）或 False（未点赞）
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_deleted:
            return CommentLike.objects.filter(comment=obj, user=request.user, is_like=True).exists()
        return False

    def get_disliked(self, obj):
        """
        判断当前用户是否点踩

        Args:
            obj: Comment 对象

        Returns:
            True（已点踩）或 False（未点踩）
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_deleted:
            return CommentLike.objects.filter(comment=obj, user=request.user, is_like=False).exists()
        return False


class CommentSerializer(serializers.ModelSerializer):
    """
    评论序列化器

    用于序列化一级评论，包含子评论列表和动态状态字段。

    设计特点：
        - 递归获取所有子孙评论（扁平化存储）
        - 包含子评论计数
        - 包含当前用户的点赞/点踩状态

    动态字段：
        - replies: 子评论列表（递归获取所有层级）
        - reply_count: 子孙评论总数
        - liked: 当前用户是否点赞
        - disliked: 当前用户是否点踩
    """
    author = ProfileListSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id', 'post', 'author', 'parent', 'content', 'like_count',
            'dislike_count', 'is_deleted', 'is_hidden', 'created_at',
            'updated_at', 'replies', 'reply_count', 'liked', 'disliked'
        )
        read_only_fields = ('like_count', 'dislike_count', 'created_at',
                            'updated_at', 'is_deleted', 'is_hidden')

    def get_replies(self, obj):
        """
        递归获取主评论下的所有子孙回复

        使用深度优先遍历，将树形结构扁平化存储为列表。
        前端根据 parent_id 重建树形结构。

        设计原因：
            - 递归获取所有层级的子评论
            - 扁平化存储便于前端处理
            - 使用 ReplySerializer（轻量级）序列化子评论

        Args:
            obj: Comment 对象（必须是一级评论）

        Returns:
            扁平化的子评论列表
        """
        # 只有一级评论才返回子评论列表
        if obj.parent is not None or obj.is_deleted:
            return []

        all_descendants = []

        def collect_replies(parent_comment):
            # 获取当前父节点下的直接子回复（排除已删除和隐藏的）
            direct_replies = parent_comment.replies.filter(
                is_deleted=False, is_hidden=False
            ).order_by('created_at')

            for reply in direct_replies:
                all_descendants.append(reply)
                # 递归搜集这个回复下的子回复（三级、四级...）
                collect_replies(reply)

        # 开始递归搜集
        collect_replies(obj)

        # 使用 ReplySerializer 序列化整个打平的子孙评论列表
        return ReplySerializer(all_descendants, many=True, context=self.context).data

    @extend_schema_field(serializers.IntegerField)
    def get_reply_count(self, obj):
        """
        计算子孙评论总数

        递归计算当前评论下所有层级的子评论数量。

        Args:
            obj: Comment 对象

        Returns:
            子孙评论总数
        """
        def count_descendants(parent_comment):
            # 计算直接子评论数量
            direct_count = parent_comment.replies.filter(is_deleted=False, is_hidden=False).count()
            # 递归计算每个子评论的子孙数量
            for reply in parent_comment.replies.filter(is_deleted=False, is_hidden=False):
                direct_count += count_descendants(reply)
            return direct_count

        # 只有一级评论才计算子评论数量
        if obj.parent is None:
            return count_descendants(obj)
        return 0

    @extend_schema_field(serializers.BooleanField)
    def get_liked(self, obj):
        """
        判断当前用户是否点赞

        Args:
            obj: Comment 对象

        Returns:
            True（已点赞）或 False（未点赞）
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_deleted:
            return CommentLike.objects.filter(
                comment=obj, user=request.user, is_like=True
            ).exists()
        return False

    @extend_schema_field(serializers.BooleanField)
    def get_disliked(self, obj):
        """
        判断当前用户是否点踩

        Args:
            obj: Comment 对象

        Returns:
            True（已点踩）或 False（未点踩）
        """
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_deleted:
            return CommentLike.objects.filter(
                comment=obj, user=request.user, is_like=False
            ).exists()
        return False

    def create(self, validated_data):
        """
        创建评论

        设置作者为当前用户。

        Args:
            validated_data: 验证后的表单数据

        Returns:
            创建的 Comment 对象
        """
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ReportSerializer(serializers.ModelSerializer):
    """
    举报序列化器

    用于序列化举报记录，包含举报原因和处理状态。

    设计特点：
        - 举报者字段只读，自动设置为当前用户
        - 处理状态字段只读，由管理员更新

    字段：
        - id: 举报ID
        - content_type: 内容类型（帖子/评论）
        - object_id: 内容ID
        - reporter: 举报者（只读）
        - reason: 举报原因
        - description: 详细描述
        - status: 处理状态（只读）
        - created_at: 创建时间（只读）
    """
    reporter = ProfileListSerializer(read_only=True)

    class Meta:
        model = Report
        fields = ('id', 'content_type', 'object_id', 'reporter', 'reason',
                  'description', 'status', 'created_at')
        read_only_fields = ('status', 'created_at', 'reporter')

    def create(self, validated_data):
        """
        创建举报记录

        设置举报者为当前用户。

        Args:
            validated_data: 验证后的表单数据

        Returns:
            创建的 Report 对象
        """
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)