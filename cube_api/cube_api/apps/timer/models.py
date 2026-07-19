from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TimerRecord(models.Model):
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