# -*- coding: utf-8 -*-
"""
Home 模块测试

测试首页模块的核心功能，包括：
    - 首页数据聚合接口
    - 轮播图、公告等展示内容
"""
from django.test import TestCase
from rest_framework import status


class HomeAPITest(TestCase):
    """首页 API 测试"""

    def test_home_page_api(self):
        """测试首页数据接口"""
        response = self.client.get('/api/home/homepage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_banner_list_api(self):
        """测试轮播图列表接口"""
        response = self.client.get('/api/home/banners/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_announcement_list_api(self):
        """测试公告列表接口"""
        response = self.client.get('/api/home/announcements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
