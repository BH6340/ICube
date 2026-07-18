# forum/serializers.py
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import Post, Tag, Comment, PostLike, CommentLike, PostCollect, Report
from apps.accounts.serializers import ProfileListSerializer, UserSerializer


class TagSerializer(serializers.ModelSerializer):
    """标签序列化器"""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'use_count')


class PostListSerializer(serializers.ModelSerializer):
    """帖子列表序列化器（轻量级）"""
    author = ProfileListSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'author', 'view_count', 'like_count',
            'comment_count', 'tags', 'is_pinned', 'is_essence',
            'created_at', 'updated_at'
        )


class PostSerializer(serializers.ModelSerializer):
    """帖子详情序列化器"""
    author = ProfileListSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_collected = serializers.SerializerMethodField()
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
            'comment_count', 'collect_count', 'tags', 'tag_ids', 'is_pinned', 'is_essence',
            'is_closed', 'status', 'report_count', 'created_at', 'updated_at',
            'is_liked', 'is_collected'
        )
        read_only_fields = ('view_count', 'like_count', 'comment_count',
                            'collect_count', 'report_count', 'status', 'created_at', 'updated_at')

    @extend_schema_field(serializers.BooleanField)
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user).exists()
        return False

    @extend_schema_field(serializers.BooleanField)
    def get_is_collected(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostCollect.objects.filter(post=obj, user=request.user).exists()
        return False

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        validated_data['author'] = self.context['request'].user
        post = super().create(validated_data)

        # 处理标签
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids)
            post.tags.set(tags)
            for tag in tags:
                tag.increment_use_count()

        return post

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        post = super().update(instance, validated_data)

        if tag_ids is not None:
            post.tags.set(tag_ids)

        return post


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """创建/更新帖子的序列化器"""
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    content_file = serializers.FileField(write_only=True, required=False, help_text='上传.md文件')

    class Meta:
        model = Post
        fields = ('id', 'title', 'content', 'content_md', 'content_file', 'tag_ids', 'tags')
        # 💡 确保 id 是只读的，防止作为接口输入参数
        read_only_fields = ('id',)

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("标题至少3个字符")
        if len(value) > 200:
            raise serializers.ValidationError("标题不能超过200个字符")
        return value.strip()

    def validate_content(self, value):
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("内容至少10个字符")
        return value.strip() if value else ''

    def validate_content_file(self, value):
        """验证上传的.md文件"""
        if not value.name.endswith('.md'):
            raise serializers.ValidationError("只支持.md格式的文件")
        if value.size > 1024 * 1024 * 5:  # 5MB
            raise serializers.ValidationError("文件大小不能超过5MB")
        return value

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        content_file = validated_data.pop('content_file', None)

        # 处理文件上传
        if content_file:
            content = content_file.read().decode('utf-8')
            validated_data['content'] = content
            validated_data['content_md'] = content

        validated_data['author'] = self.context['request'].user
        post = Post.objects.create(**validated_data)

        if tag_ids:
            post.tags.set(tag_ids)

        return post

    # 💡 ✨ 修复核心：重写 update 方法，确保更新标签后能重新加载关联的 tags 对象
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        post = super().update(instance, validated_data)

        if tag_ids is not None:
            post.tags.set(tag_ids)

        return post


# 💡 标注修改：重写 ReplySerializer，使其包含子评论所需的动态状态字段（赞、踩、被回复人）
class ReplySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    reply_to_name = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()  # 对应前端 comment.liked
    disliked = serializers.SerializerMethodField()  # 对应前端 comment.disliked

    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'created_at', 'author', 'parent',
            'reply_to_name', 'like_count', 'dislike_count', 'liked', 'disliked'
        ]

    def get_reply_to_name(self, obj):
        # 💡 修改：如果当前子回复存在父评论，且父评论有作者，则返回父评论作者的用户名
        if obj.parent and obj.parent.author:
            return obj.parent.author.username
        return None

    def get_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_deleted:
            return CommentLike.objects.filter(comment=obj, user=request.user, is_like=True).exists()
        return False

    def get_disliked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_deleted:
            return CommentLike.objects.filter(comment=obj, user=request.user, is_like=False).exists()
        return False


class CommentSerializer(serializers.ModelSerializer):
    """评论序列化器"""
    author = ProfileListSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()  # 💡 修改：改名为 liked，保持与服务层和前端命名高度一致
    disliked = serializers.SerializerMethodField()  # 💡 修改：改名为 disliked，保持与服务层和前端命名高度一致

    class Meta:
        model = Comment
        fields = (
            'id', 'post', 'author', 'parent', 'content', 'like_count',
            'dislike_count', 'is_deleted', 'is_hidden', 'created_at',
            'updated_at', 'replies', 'reply_count', 'liked', 'disliked'
        )
        read_only_fields = ('like_count', 'dislike_count', 'created_at',
                            'updated_at', 'is_deleted', 'is_hidden')

    # 💡 标注修改：核心变动。递归捞取当前一级评论下所有深度的子孙回复
    def get_replies(self, obj):
        """递归获取主评论下的所有子孙回复"""
        if obj.parent is not None or obj.is_deleted:
            return []

        all_descendants = []

        def collect_replies(parent_comment):
            # 获取当前父节点下的直接子回复
            direct_replies = parent_comment.replies.filter(
                is_deleted=False, is_hidden=False
            ).order_by('created_at')

            for reply in direct_replies:
                all_descendants.append(reply)
                # 递归搜集这个回复下的子回复（三级、四级...）
                collect_replies(reply)

        # 开始搜集
        collect_replies(obj)

        # 使用上方的 ReplySerializer 序列化整个打平的子孙评论列表
        return ReplySerializer(all_descendants, many=True, context=self.context).data

    @extend_schema_field(serializers.IntegerField)
    def get_reply_count(self, obj):
        # 💡 标注修改：计算这栋楼里包含的所有子孙评论总数，而非单指二级评论数
        def count_descendants(parent_comment):
            direct_count = parent_comment.replies.filter(is_deleted=False, is_hidden=False).count()
            for reply in parent_comment.replies.filter(is_deleted=False, is_hidden=False):
                direct_count += count_descendants(reply)
            return direct_count

        if obj.parent is None:
            return count_descendants(obj)
        return 0

    @extend_schema_field(serializers.BooleanField)
    def get_liked(self, obj):
        """准确对应 fields 中的 'liked'"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_deleted:
            return CommentLike.objects.filter(
                comment=obj, user=request.user, is_like=True
            ).exists()
        return False

    @extend_schema_field(serializers.BooleanField)
    def get_disliked(self, obj):  # 💡 ✅ 标注修改：去掉原来的 _is_，改成 get_disliked
        """准确对应 fields 中的 'disliked'"""
        request = self.context.get('request')
        if request and request.user.is_authenticated and not obj.is_deleted:
            return CommentLike.objects.filter(
                comment=obj, user=request.user, is_like=False
            ).exists()
        return False

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ReportSerializer(serializers.ModelSerializer):
    """举报序列化器"""
    reporter = ProfileListSerializer(read_only=True)

    class Meta:
        model = Report
        fields = ('id', 'content_type', 'object_id', 'reporter', 'reason',
                  'description', 'status', 'created_at')
        read_only_fields = ('status', 'created_at', 'reporter')

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)