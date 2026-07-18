# forum/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Comment, Tag


@receiver(post_save, sender=Comment)
def update_post_comment_count(sender, instance, created, **kwargs):
    """更新帖子的评论数"""
    if created and not instance.is_deleted:
        post = instance.post
        post.comment_count = post.comments.filter(is_deleted=False, is_hidden=False).count()
        post.save(update_fields=['comment_count'])


@receiver(post_delete, sender=Comment)
def update_post_comment_count_on_delete(sender, instance, **kwargs):
    """删除评论时更新帖子评论数"""
    post = instance.post
    post.comment_count = post.comments.filter(is_deleted=False, is_hidden=False).count()
    post.save(update_fields=['comment_count'])


@receiver(post_save, sender=Tag)
def update_tag_use_count(sender, instance, **kwargs):
    """更新标签使用次数"""
    instance.use_count = instance.posts.count()
    instance.save(update_fields=['use_count'])