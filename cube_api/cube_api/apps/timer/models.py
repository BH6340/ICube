# -*- coding: utf-8 -*-
"""
计时器模块数据模型

定义计时记录的数据结构，支持多种魔方类型和还原方法的统计。

设计特点：
    - **魔方类型枚举**：支持二阶、三阶、四阶、五阶及其他类型
    - **还原方法枚举**：支持层先法、CFOP、桥式、ZBLL及其他方法
    - **毫秒级精度**：使用毫秒存储还原时间，保证精度
    - **打乱公式存储**：scramble 字段记录打乱公式，便于复盘
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimerRecord(models.Model):
    """
    计时记录模型

    存储用户的魔方还原计时记录，支持按魔方类型和还原方法分组统计。

    魔方类型（CUBE_TYPE_CHOICES）：
        - 2x2: 二阶魔方
        - 3x3: 三阶魔方（默认）
        - 4x4: 四阶魔方
        - 5x5: 五阶魔方
        - other: 其他类型

    还原方法（METHOD_CHOICES）：
        - layer: 层先法（默认）
        - cfop: CFOP 高级方法
        - roux: 桥式方法
        - zbll: ZBLL 方法
        - other: 其他方法

    设计要点：
        - **毫秒存储**：time_ms 使用整数存储毫秒，避免浮点精度问题
        - **打乱公式**：scramble 字段记录打乱序列，便于用户复盘
        - **排序规则**：按创建时间倒序，最新记录优先显示
    """
    CUBE_TYPE_CHOICES = [
        ('2x2', '二阶魔方'),
        ('3x3', '三阶魔方'),
        ('4x4', '四阶魔方'),
        ('5x5', '五阶魔方'),
        ('other', '其他'),
    ]

    METHOD_CHOICES = [
        ('layer', '层先法'),
        ('cfop', 'CFOP'),
        ('roux', '桥式'),
        ('zbll', 'ZBLL'),
        ('other', '其他'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='timer_records',
        verbose_name='用户'
    )
    cube_type = models.CharField(
        '魔方类型',
        max_length=10,
        choices=CUBE_TYPE_CHOICES,
        default='3x3'
    )
    method = models.CharField(
        '还原方法',
        max_length=20,
        choices=METHOD_CHOICES,
        default='layer'
    )
    time_ms = models.IntegerField('还原时间(毫秒)')
    scramble = models.TextField('打乱公式', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        app_label = 'timer'
        db_table = 'timer_record'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.cube_type} - {self.time_ms}ms'