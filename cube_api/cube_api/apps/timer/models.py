# -*- coding: utf-8 -*-
"""
计时器模块数据模型

定义计时记录和智能魔方设备的数据结构。

设计特点：
    - **魔方类型枚举**：支持二阶、三阶、四阶、五阶及其他类型
    - **还原方法枚举**：支持层先法、CFOP、桥式、ZBLL及其他方法
    - **计时方式枚举**：手动计时 / 智能魔方
    - **毫秒级精度**：使用毫秒存储还原时间，保证精度
    - **打乱公式存储**：scramble 字段记录打乱公式，便于复盘
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SmartCubeDevice(models.Model):
    """
    智能魔方设备模型

    存储用户连接过的智能魔方设备信息，便于下次自动连接无需手动输入 MAC。
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='smart_cube_devices',
        verbose_name='用户'
    )
    mac_address = models.CharField(
        'MAC 地址',
        max_length=20
    )
    name = models.CharField(
        '设备名称',
        max_length=50,
        blank=True
    )
    last_connected_at = models.DateTimeField(
        '最后连接时间',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(
        '是否启用',
        default=True
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        app_label = 'timer'
        db_table = 'smart_cube_device'
        ordering = ['-last_connected_at']
        verbose_name = '智能魔方设备'
        verbose_name_plural = '智能魔方设备'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'mac_address'],
                name='unique_user_mac'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.name or self.mac_address}'


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
        - cfop: CFOP
        - roux: 桥式
        - zbll: ZBLL
        - other: 其他方法

    计时方式（TIMING_MODE_CHOICES）：
        - manual: 手动计时（默认）
        - smart: 智能魔方

    设计要点：
        - **毫秒存储**：time_ms 使用整数存储毫秒，避免浮点精度问题
        - **打乱公式**：scramble 字段记录打乱序列，便于用户复盘
        - **排序规则**：按创建时间倒序，最新记录优先显示
        - **向后兼容**：所有新增字段均为 nullable，旧数据自动归入 manual 模式
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

    TIMING_MODE_CHOICES = [
        ('manual', '手动计时'),
        ('smart', '智能魔方'),
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
    timing_mode = models.CharField(
        '计时方式',
        max_length=10,
        choices=TIMING_MODE_CHOICES,
        default='manual'
    )
    time_ms = models.IntegerField('还原时间(毫秒)')
    scramble = models.TextField('打乱公式', blank=True)
    solve_sequence = models.TextField('复原步骤序列', blank=True, null=True)
    observation_time_ms = models.IntegerField('观察时间(毫秒)', null=True, blank=True)
    move_count = models.IntegerField('复原步数', null=True, blank=True)
    is_dnf = models.BooleanField('是否 DNF', default=False)
    device = models.ForeignKey(
        SmartCubeDevice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='records',
        verbose_name='关联设备'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        app_label = 'timer'
        db_table = 'timer_record'
        ordering = ['-created_at']
        verbose_name = '计时记录'
        verbose_name_plural = '计时记录'

    def __str__(self):
        mode = dict(self.TIMING_MODE_CHOICES).get(self.timing_mode, '')
        return f'{self.user.username} - {self.cube_type} - {mode} - {self.time_ms}ms'
