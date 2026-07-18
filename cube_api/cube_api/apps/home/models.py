# apps/home/models.py
from django.db import models

class NavigationMenu(models.Model):
    CATEGORY_CHOICES = [
        ('main', '主导航栏'),
        ('profile', '个人中心导航栏'),
    ]

    index = models.CharField(max_length=20, unique=True, verbose_name="菜单唯一标识")
    label = models.CharField(max_length=50, verbose_name="菜单名称")
    path = models.CharField(max_length=250, verbose_name="跳转路径")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='main', verbose_name="菜单分类")
    sort_order = models.IntegerField(default=0, verbose_name="排序（越小越靠前）")
    match_paths = models.JSONField(default=list, blank=True, verbose_name="匹配路径集") 

    class Meta:
        ordering = ['sort_order']
        verbose_name = "导航菜单"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"[{self.get_category_display()}] {self.label}"