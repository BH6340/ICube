# -*- coding: utf-8 -*-
"""
Formula 应用测试基类

提供 formula 模块测试的通用工具和配置，包括：
    - 测试用户创建
    - 测试分类、状态、公式创建
    - API 客户端认证
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.formula.models import CubeCategory, CubeState, Formula

User = get_user_model()


class FormulaBaseTestCase(TestCase):
    """Formula 测试基类"""

    def setUp(self):
        """每个测试方法执行前的设置"""
        super().setUp()
        cache.clear()

        # 创建 API 客户端
        self.client = APIClient()

        # 创建测试用户
        self.user = self.create_test_user(
            email='formula_test@example.com',
            password='test123456',
            username='formula_tester'
        )

        # 创建管理员用户
        self.admin_user = self.create_test_admin(
            email='formula_admin@example.com',
            password='admin123456',
            username='formula_admin'
        )

        # 创建测试分类
        self.category = self.create_test_category(
            order=3,
            method='CFOP',
            phase='OLL',
            name='OLL 分类'
        )

        # 创建测试状态
        self.state = self.create_test_state(
            name='OLL-01',
            state_definition=self._get_valid_state_definition(),
            category=self.category
        )

        # 创建测试公式
        self.formula = self.create_test_formula(
            name='测试公式',
            notation="R U R' U'",
            category=self.category,
            target_state=self.state
        )

    def tearDown(self):
        """每个测试方法执行后的清理"""
        cache.clear()
        super().tearDown()

    # ============ 辅助方法 ============

    def create_test_user(self, email, password, username, **kwargs):
        """创建普通测试用户"""
        return User.objects.create_user(
            email=email,
            password=password,
            username=username,
            **kwargs
        )

    def create_test_admin(self, email, password, username, **kwargs):
        """创建管理员测试用户"""
        return User.objects.create_superuser(
            email=email,
            password=password,
            username=username,
            **kwargs
        )

    def create_test_category(self, order=3, method='CFOP', phase='OLL', name='测试分类', **kwargs):
        """创建测试分类"""
        return CubeCategory.objects.create(
            order=order,
            method=method,
            phase=phase,
            name=name,
            **kwargs
        )

    def create_test_state(self, name='测试状态', state_definition=None, category=None, **kwargs):
        """创建测试状态"""
        if state_definition is None:
            state_definition = self._get_valid_state_definition()
        return CubeState.objects.create(
            name=name,
            state_definition=state_definition,
            category=category,
            **kwargs
        )

    def create_test_formula(self, name='测试公式', notation="R U R' U'", category=None, target_state=None, **kwargs):
        """创建测试公式"""
        return Formula.objects.create(
            name=name,
            notation=notation,
            category=category or self.category,
            target_state=target_state or self.state,
            **kwargs
        )

    def _get_valid_state_definition(self):
        """获取有效的状态定义（3阶27块，中心块标准配色）"""
        center_colors = {
            (0, 1, 0): ('U', 'Y'),
            (0, -1, 0): ('D', 'W'),
            (0, 0, 1): ('F', 'B'),
            (0, 0, -1): ('B', 'G'),
            (-1, 0, 0): ('L', 'O'),
            (1, 0, 0): ('R', 'R'),
        }
        blocks = []
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                for k in [-1, 0, 1]:
                    faces = {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}
                    if (i, j, k) in center_colors:
                        face, color = center_colors[(i, j, k)]
                        faces[face] = color
                    blocks.append({'pos': [i, j, k], 'faces': faces})
        return {
            'order': 3,
            'blocks': blocks,
        }

    def authenticate(self, user=None):
        """认证用户"""
        if user is None:
            user = self.user
        self.client.force_authenticate(user=user)
        return self.client

    def authenticate_admin(self):
        """认证为管理员"""
        self.client.force_authenticate(user=self.admin_user)
        return self.client

    def get_valid_formula_data(self, **kwargs):
        """获取有效的公式创建数据"""
        data = {
            'name': kwargs.get('name', '新公式'),
            'notation': kwargs.get('notation', "R U R' U'"),
            'category_id': kwargs.get('category_id', self.category.id),
            'difficulty': kwargs.get('difficulty', 2),
        }
        return data

    def get_valid_category_data(self, **kwargs):
        """获取有效的分类创建数据"""
        data = {
            'order': kwargs.get('order', 3),
            'method': kwargs.get('method', 'CFOP'),
            'phase': kwargs.get('phase', 'PLL'),
            'name': kwargs.get('name', '新分类'),
        }
        return data


class FormulaAPITestCase(FormulaBaseTestCase):
    """Formula API 测试基类（自动认证普通用户）"""

    def setUp(self):
        super().setUp()
        self.authenticate()


class FormulaAdminAPITestCase(FormulaBaseTestCase):
    """Formula API 测试基类（自动认证管理员）"""

    def setUp(self):
        super().setUp()
        self.authenticate_admin()
