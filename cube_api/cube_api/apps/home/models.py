# -*- coding: utf-8 -*-
"""
首页导航模块数据模型

定义导航菜单的数据结构，支持动态配置前端导航栏。

设计特点：
    - **菜单分类**：支持主导航栏（main）和个人中心导航栏（profile）
    - **唯一标识**：index 字段确保菜单在前后端的一致性引用
    - **路由匹配**：match_paths 用于前端路由高亮匹配
    - **排序控制**：sort_order 控制菜单显示顺序
"""

from django.db import models


class NavigationMenu(models.Model):
    """
    导航菜单模型

    存储前端导航栏的菜单配置，支持动态管理。

    菜单分类：
        - main: 主导航栏（顶部导航）
        - profile: 个人中心导航栏（侧边栏）

    设计要点：
        - **index 唯一标识**：用于前端组件引用，确保前后端一致性
        - **match_paths 路由匹配**：数组形式，支持多个路由路径匹配高亮
        - **sort_order 排序**：数值越小越靠前，便于调整菜单顺序
    """
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


class Banner(models.Model):
    """
    轮播图模型

    存储首页轮播图数据，支持后台动态管理。

    设计要点：
        - **图片存储**: 使用 ImageField 存储轮播图图片
        - **跳转链接**: link 字段支持外部链接和内部路由
        - **排序控制**: sort_order 控制轮播图显示顺序，数值越小越靠前
        - **状态管理**: is_active 字段控制轮播图是否显示
    """
    title = models.CharField(max_length=100, verbose_name="标题")
    description = models.CharField(max_length=255, blank=True, verbose_name="描述")
    image = models.ImageField(upload_to='banners/', verbose_name="轮播图图片")
    link = models.URLField(max_length=500, blank=True, verbose_name="跳转链接")
    sort_order = models.IntegerField(default=0, verbose_name="排序（越小越靠前）")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        ordering = ['sort_order', '-created_at']
        verbose_name = "轮播图"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title