# -*- coding: utf-8 -*-
"""
论坛信号处理器

该模块定义了 Django 信号的接收器，用于处理模型变更后的副作用。

信号处理逻辑：
    - 评论创建/删除：自动更新帖子的评论数
    - 标签保存：自动更新标签的使用次数

设计原因：
    - 使用信号机制解耦业务逻辑，避免在多个地方重复更新计数
    - 确保计数的准确性和一致性
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Comment, Tag


@receiver(post_save, sender=Comment)
def update_post_comment_count(sender, instance, created, **kwargs):
    """
    更新帖子的评论数（创建评论时）

    当新评论被创建且未被删除时，更新所属帖子的评论数。

    设计原因：
        - 评论创建后需要立即更新帖子的评论数，保持数据一致性
        - 使用 post_save 信号确保事务提交后再更新
        - 排除已删除的评论，避免计数不准确

    Args:
        sender: 发送信号的模型类（Comment）
        instance: 被保存的评论实例
        created: 是否是新创建的记录
    """
    if created and not instance.is_deleted:
        post = instance.post
        # 重新计算评论数（排除已删除和隐藏的评论）
        post.comment_count = post.comments.filter(is_deleted=False, is_hidden=False).count()
        post.save(update_fields=['comment_count'])


@receiver(post_delete, sender=Comment)
def update_post_comment_count_on_delete(sender, instance, **kwargs):
    """
    删除评论时更新帖子评论数

    当评论被物理删除时，更新所属帖子的评论数。

    设计原因：
        - 评论删除后需要立即更新帖子的评论数
        - 使用 post_delete 信号确保删除完成后再更新

    Args:
        sender: 发送信号的模型类（Comment）
        instance: 被删除的评论实例
    """
    post = instance.post
    # 重新计算评论数（排除已删除和隐藏的评论）
    post.comment_count = post.comments.filter(is_deleted=False, is_hidden=False).count()
    post.save(update_fields=['comment_count'])


@receiver(post_save, sender=Tag)
def update_tag_use_count(sender, instance, **kwargs):
    """
    更新标签使用次数

    当标签被保存时，重新计算该标签的使用次数。

    设计原因：
        - 标签关联/取消关联帖子后需要更新使用次数
        - 使用 post_save 信号确保每次保存后都更新计数
        - 避免在多个地方手动更新，保持数据一致性

    Args:
        sender: 发送信号的模型类（Tag）
        instance: 被保存的标签实例
    """
    # 重新计算标签的使用次数
    instance.use_count = instance.posts.count()
    instance.save(update_fields=['use_count'])