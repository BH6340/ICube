# -*- coding: utf-8 -*-
"""
Formula 模块 API 接口测试

测试 formula 模块的核心 API 接口，包括：
    - 分类 CRUD 接口
    - 状态 CRUD 接口
    - 公式 CRUD 接口
    - 收藏接口
    - 公式匹配接口
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import status

from .base import FormulaBaseTestCase, FormulaAPITestCase, FormulaAdminAPITestCase
from apps.formula.models import CubeCategory, CubeState, Formula, FormulaTag, FormulaCollection

User = get_user_model()


class CubeCategoryAPITest(FormulaBaseTestCase):
    """魔方分类 API 测试"""

    def test_list_categories_anonymous(self):
        """测试匿名用户获取分类列表"""
        response = self.client.get('/api/formula/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_categories_authenticated(self):
        """测试认证用户获取分类列表"""
        self.authenticate()
        response = self.client.get('/api/formula/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_category_authenticated(self):
        """测试认证用户创建分类"""
        self.authenticate()
        data = self.get_valid_category_data()
        response = self.client.post('/api/formula/categories/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['data']['is_custom'])

    def test_create_category_anonymous_fails(self):
        """测试匿名用户创建分类失败"""
        data = self.get_valid_category_data()
        response = self.client.post('/api/formula/categories/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_category(self):
        """测试获取单个分类详情"""
        response = self.client.get(f'/api/formula/categories/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_own_custom_category(self):
        """测试更新自己的自定义分类"""
        self.authenticate()
        # 创建自定义分类
        response = self.client.post('/api/formula/categories/', self.get_valid_category_data(), format='json')
        custom_id = response.data['data']['id']

        # 更新分类
        update_data = {'name': '更新后的分类名'}
        response = self.client.patch(f'/api/formula/categories/{custom_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_system_category_fails(self):
        """测试更新系统分类失败"""
        self.authenticate()
        update_data = {'name': '不应允许更新'}
        response = self.client.patch(f'/api/formula/categories/{self.category.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_custom_category(self):
        """测试删除自己的自定义分类"""
        self.authenticate()
        # 创建自定义分类
        response = self.client.post('/api/formula/categories/', self.get_valid_category_data(), format='json')
        custom_id = response.data['data']['id']

        # 删除分类
        response = self.client.delete(f'/api/formula/categories/{custom_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_system_category_fails(self):
        """测试删除系统分类失败"""
        self.authenticate()
        response = self.client.delete(f'/api/formula/categories/{self.category.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_my_custom_categories(self):
        """测试获取当前用户的自定义分类"""
        self.authenticate()
        response = self.client.get('/api/formula/categories/my_custom/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CubeStateAPITest(FormulaBaseTestCase):
    """魔方状态 API 测试"""

    def test_list_states_anonymous(self):
        """测试匿名用户获取状态列表"""
        response = self.client.get('/api/formula/states/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_state_as_admin(self):
        """测试管理员创建状态"""
        self.authenticate_admin()
        data = {
            'name': '新状态',
            'state_definition': {
                'order': 3,
                'blocks': [
                    {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
                ]
            },
            'category': self.category.id
        }
        response = self.client.post('/api/formula/states/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_state_as_user_fails(self):
        """测试普通用户创建状态失败"""
        self.authenticate()
        data = {
            'name': '不应创建',
            'state_definition': {'order': 3, 'blocks': []},
        }
        response = self.client.post('/api/formula/states/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_state(self):
        """测试获取单个状态详情"""
        response = self.client.get(f'/api/formula/states/{self.state.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FormulaAPITest(FormulaBaseTestCase):
    """公式 API 测试"""

    def test_list_formulas_anonymous(self):
        """测试匿名用户获取公式列表"""
        response = self.client.get('/api/formula/formulas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_formula_increments_view_count(self):
        """测试获取公式详情时浏览量增加"""
        initial_count = self.formula.view_count
        response = self.client.get(f'/api/formula/formulas/{self.formula.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 刷新数据库检查浏览量是否增加
        self.formula.refresh_from_db()
        self.assertEqual(self.formula.view_count, initial_count + 1)

    def test_create_formula_authenticated(self):
        """测试认证用户创建公式"""
        self.authenticate()
        data = self.get_valid_formula_data()
        response = self.client.post('/api/formula/formulas/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 普通用户创建的公式应为自定义公式
        self.assertTrue(response.data['data']['is_custom'])

    def test_create_formula_anonymous_fails(self):
        """测试匿名用户创建公式失败"""
        data = self.get_valid_formula_data()
        response = self.client.post('/api/formula/formulas/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_custom_formula(self):
        """测试更新自己的自定义公式"""
        self.authenticate()
        # 创建自定义公式
        data = self.get_valid_formula_data()
        create_response = self.client.post('/api/formula/formulas/', data, format='json')
        formula_id = create_response.data['data']['id']

        # 更新公式
        update_data = {'name': '更新后的公式名'}
        response = self.client.patch(f'/api/formula/formulas/{formula_id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_system_formula_as_user_fails(self):
        """测试普通用户更新系统公式失败"""
        self.authenticate()
        update_data = {'name': '不应修改'}
        response = self.client.patch(f'/api/formula/formulas/{self.formula.id}/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_custom_formula(self):
        """测试删除自己的自定义公式"""
        self.authenticate()
        # 创建自定义公式
        data = self.get_valid_formula_data()
        create_response = self.client.post('/api/formula/formulas/', data, format='json')
        formula_id = create_response.data['data']['id']

        # 删除公式
        response = self.client.delete(f'/api/formula/formulas/{formula_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_custom_formulas(self):
        """测试获取当前用户的自定义公式"""
        self.authenticate()
        # 创建自定义公式
        data = self.get_valid_formula_data()
        self.client.post('/api/formula/formulas/', data, format='json')

        response = self.client.get('/api/formula/formulas/my_custom/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authors_list(self):
        """测试获取作者列表"""
        response = self.client.get('/api/formula/formulas/authors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('authors', response.data['data'])

    def test_simple_list(self):
        """测试获取精简公式列表"""
        response = self.client.get('/api/formula/formulas/simple_list/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_formulas_by_category(self):
        """测试按分类筛选公式"""
        response = self.client.get(f'/api/formula/formulas/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_formulas(self):
        """测试搜索公式"""
        response = self.client.get('/api/formula/formulas/?search=测试')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FormulaMatchAPITest(FormulaBaseTestCase):
    """公式匹配 API 测试"""

    def test_match_formulas_authenticated(self):
        """测试认证用户进行公式匹配"""
        self.authenticate()
        state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
            ]
        }
        response = self.client.post('/api/formula/formulas/match/', {'state_definition': state}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_match_formulas_anonymous_fails(self):
        """测试匿名用户进行公式匹配失败"""
        state = {'order': 3, 'blocks': []}
        response = self.client.post('/api/formula/formulas/match/', {'state_definition': state}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FormulaCollectionAPITest(FormulaBaseTestCase):
    """公式收藏 API 测试"""

    def setUp(self):
        super().setUp()
        self.authenticate()

    def test_list_collections(self):
        """测试获取收藏列表"""
        response = self.client.get('/api/formula/collections/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_collection(self):
        """测试收藏公式"""
        data = {'formula': self.formula.id}
        response = self.client.post('/api/formula/collections/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_collection_idempotent(self):
        """测试重复收藏的幂等性"""
        data = {'formula': self.formula.id}
        response1 = self.client.post('/api/formula/collections/', data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        response2 = self.client.post('/api/formula/collections/', data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

    def test_create_collection_nonexistent_formula(self):
        """测试收藏不存在的公式"""
        data = {'formula': 99999}
        response = self.client.post('/api/formula/collections/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_collection_without_formula_id(self):
        """测试无公式ID的收藏请求"""
        response = self.client.post('/api/formula/collections/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_collection(self):
        """测试取消收藏"""
        # 先收藏
        self.client.post('/api/formula/collections/', {'formula': self.formula.id}, format='json')

        # 取消收藏
        response = self.client.delete(f'/api/formula/collections/{self.formula.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_nonexistent_collection(self):
        """测试取消不存在的收藏"""
        response = self.client.delete('/api/formula/collections/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_collections_by_category(self):
        """测试按分类筛选收藏"""
        response = self.client.get(f'/api/formula/collections/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_collections_by_difficulty(self):
        """测试按难度筛选收藏"""
        response = self.client.get('/api/formula/collections/?difficulty=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FormulaTagAPITest(FormulaBaseTestCase):
    """公式标签 API 测试"""

    def test_list_tags_anonymous(self):
        """测试匿名用户获取标签列表"""
        response = self.client.get('/api/formula/tags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_tag_as_admin(self):
        """测试管理员创建标签"""
        self.authenticate_admin()
        data = {'name': '测试标签', 'color': '#FF5722'}
        response = self.client.post('/api/formula/tags/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_tag_as_user_fails(self):
        """测试普通用户创建标签失败"""
        self.authenticate()
        data = {'name': '不应创建', 'color': '#FF5722'}
        response = self.client.post('/api/formula/tags/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
