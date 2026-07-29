# -*- coding: utf-8 -*-
"""
Formula 模块模型测试

测试 formula 模块的核心模型，包括：
    - CubeCategory: 魔方分类
    - CubeState: 魔方状态
    - Formula: 公式
    - FormulaTag/FormulaTagRelation: 标签与关联
    - FormulaCollection: 公式收藏
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.formula.models import (
    CubeCategory, CubeState, Formula, FormulaTag,
    FormulaTagRelation, FormulaCollection
)

User = get_user_model()


class CubeCategoryModelTest(TestCase):
    """魔方分类模型测试"""

    def setUp(self):
        """创建测试数据"""
        self.category_data = {
            'order': 3,
            'method': 'CFOP',
            'phase': 'OLL',
            'name': 'OLL 分类'
        }

    def test_create_category_success(self):
        """测试创建分类成功"""
        category = CubeCategory.objects.create(**self.category_data)

        self.assertEqual(category.order, 3)
        self.assertEqual(category.method, 'CFOP')
        self.assertEqual(category.phase, 'OLL')
        self.assertEqual(category.name, 'OLL 分类')
        self.assertFalse(category.is_custom)
        self.assertIsNone(category.created_by)

    def test_category_str_method(self):
        """测试 __str__ 方法"""
        category = CubeCategory.objects.create(**self.category_data)
        self.assertEqual(str(category), '3阶 CFOP OLL')

    def test_custom_category_with_created_by(self):
        """测试用户自定义分类"""
        user = User.objects.create_user(
            email='custom@example.com',
            password='testpass',
            username='customuser'
        )

        category = CubeCategory.objects.create(
            order=3,
            method='CFOP',
            phase='Custom',
            name='自定义分类',
            created_by=user,
            is_custom=True
        )

        self.assertTrue(category.is_custom)
        self.assertEqual(category.created_by, user)

    def test_category_ordering(self):
        """测试分类默认排序"""
        # 创建不同阶数的分类
        CubeCategory.objects.create(order=4, method='CFOP', phase='OLL', name='4阶分类')
        CubeCategory.objects.create(order=3, method='CFOP', phase='OLL', name='3阶分类')
        CubeCategory.objects.create(order=3, method='Layer', phase='Step1', name='层先法')

        categories = CubeCategory.objects.all()
        # 按 order, method, sort_order 排序
        self.assertEqual(categories[0].order, 3)
        self.assertEqual(categories[0].method, 'CFOP')
        self.assertEqual(categories[1].order, 3)
        self.assertEqual(categories[1].method, 'Layer')
        self.assertEqual(categories[2].order, 4)


class CubeStateModelTest(TestCase):
    """魔方状态模型测试"""

    def setUp(self):
        """创建测试数据"""
        self.state_data = {
            'name': 'OLL-01',
            'state_definition': {
                'order': 3,
                'blocks': [
                    {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
                    {'pos': [1, 1, 0], 'faces': {'U': 'Y', 'R': 'R', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
                ]
            }
        }

    def test_create_state_success(self):
        """测试创建状态成功"""
        state = CubeState.objects.create(**self.state_data)

        self.assertEqual(state.name, 'OLL-01')
        self.assertIsNotNone(state.state_definition)
        self.assertEqual(state.state_definition['order'], 3)

    def test_state_str_method(self):
        """测试 __str__ 方法"""
        state = CubeState.objects.create(**self.state_data)
        self.assertEqual(str(state), 'OLL-01')

    def test_state_name_uniqueness(self):
        """测试状态名称唯一性"""
        CubeState.objects.create(**self.state_data)

        with self.assertRaises(IntegrityError):
            CubeState.objects.create(
                name='OLL-01',
                state_definition={'order': 3, 'blocks': []}
            )

    def test_state_with_category(self):
        """测试状态关联分类"""
        category = CubeCategory.objects.create(
            order=3, method='CFOP', phase='OLL', name='OLL分类'
        )
        state = CubeState.objects.create(
            name='OLL-WithCategory',
            state_definition=self.state_data['state_definition'],
            category=category
        )

        self.assertEqual(state.category, category)
        self.assertIn(state, category.states.all())


class FormulaModelTest(TestCase):
    """公式模型测试"""

    def setUp(self):
        """创建测试数据"""
        self.category = CubeCategory.objects.create(
            order=3, method='CFOP', phase='OLL', name='OLL分类'
        )
        self.state = CubeState.objects.create(
            name='OLL-State',
            state_definition={
                'order': 3,
                'blocks': [
                    {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
                ]
            },
            category=self.category
        )

    def test_create_formula_success(self):
        """测试创建公式成功"""
        formula = Formula.objects.create(
            name='R U R\'U\'',
            notation="R U R' U'",
            category=self.category,
            target_state=self.state
        )

        self.assertEqual(formula.name, "R U R'U'")
        self.assertEqual(formula.notation, "R U R' U'")
        self.assertIsNotNone(formula.inverse_notation)  # 逆公式应自动生成
        self.assertEqual(formula.category, self.category)
        self.assertEqual(formula.target_state, self.state)
        self.assertEqual(formula.difficulty, 1)  # 默认难度

    def test_inverse_notation_auto_generation(self):
        """测试逆公式自动生成"""
        formula = Formula.objects.create(
            name='逆公式测试',
            notation="R U R' U'",
            category=self.category
        )

        # 逆公式应为 "U' R' U R"（反转并取逆）
        self.assertEqual(formula.inverse_notation, "U' R' U R")

    def test_inverse_notation_handles_various_notations(self):
        """测试不同公式记号的逆运算"""
        test_cases = [
            ("R U", "U' R'"),
            ("R2", "R2"),
            ("R U R' U'", "U' R' U R"),
            ("F R U", "U' R' F'"),
        ]

        for notation, expected_inverse in test_cases:
            formula = Formula.objects.create(
                name=f'测试-{notation}',
                notation=notation,
                category=self.category
            )
            self.assertEqual(
                formula.inverse_notation,
                expected_inverse,
                f"公式 {notation} 的逆运算应为 {expected_inverse}，实际为 {formula.inverse_notation}"
            )

    def test_formula_str_method(self):
        """测试 __str__ 方法"""
        formula = Formula.objects.create(
            name='测试公式',
            notation="R U R' U'",
            category=self.category
        )
        self.assertEqual(str(formula), '3阶 CFOP OLL - 测试公式')

    def test_formula_view_count_default(self):
        """测试浏览量默认为 0"""
        formula = Formula.objects.create(
            name='浏览量测试',
            notation="R U",
            category=self.category
        )
        self.assertEqual(formula.view_count, 0)

    def test_custom_formula_with_user(self):
        """测试用户自定义公式"""
        user = User.objects.create_user(
            email='formula_creator@example.com',
            password='testpass',
            username='formula_creator'
        )

        formula = Formula.objects.create(
            name='自定义公式',
            notation="R' F R F'",
            category=self.category,
            is_custom=True,
            created_by=user
        )

        self.assertTrue(formula.is_custom)
        self.assertEqual(formula.created_by, user)

    def test_get_pre_state_with_pre_state_definition(self):
        """测试获取前置状态（已设置 pre_state_definition）"""
        pre_state = {
            'order': 3,
            'blocks': [{'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}}]
        }
        formula = Formula.objects.create(
            name='前置状态测试',
            notation="R U",
            category=self.category,
            pre_state_definition=pre_state
        )

        result = formula.get_pre_state()
        self.assertEqual(result, pre_state)

    def test_get_pre_state_from_target_state(self):
        """测试从目标状态推导前置状态"""
        formula = Formula.objects.create(
            name='推导前置状态',
            notation="R U",
            category=self.category,
            target_state=self.state
        )

        result = formula.get_pre_state()
        self.assertIsNotNone(result)
        self.assertTrue(result['derive_from_target'])
        self.assertIn('target_state', result)
        self.assertIn('inverse_notation', result)

    def test_get_pre_state_without_any_state(self):
        """测试无任何状态时返回 None"""
        formula = Formula.objects.create(
            name='无状态公式',
            notation="R",
            category=self.category
        )

        result = formula.get_pre_state()
        self.assertIsNone(result)


class FormulaTagModelTest(TestCase):
    """公式标签模型测试"""

    def test_create_tag_success(self):
        """测试创建标签成功"""
        tag = FormulaTag.objects.create(name='难度标签', color='#FF5722')

        self.assertEqual(tag.name, '难度标签')
        self.assertEqual(tag.color, '#FF5722')

    def test_tag_str_method(self):
        """测试 __str__ 方法"""
        tag = FormulaTag.objects.create(name='测试标签')
        self.assertEqual(str(tag), '测试标签')

    def test_tag_name_uniqueness(self):
        """测试标签名称唯一性"""
        FormulaTag.objects.create(name='唯一标签')

        with self.assertRaises(IntegrityError):
            FormulaTag.objects.create(name='唯一标签')

    def test_tag_default_color(self):
        """测试标签默认颜色"""
        tag = FormulaTag.objects.create(name='默认颜色标签')
        self.assertEqual(tag.color, '#1890ff')


class FormulaTagRelationModelTest(TestCase):
    """公式标签关联测试"""

    def setUp(self):
        """创建测试数据"""
        self.category = CubeCategory.objects.create(
            order=3, method='CFOP', phase='OLL', name='测试分类'
        )
        self.formula = Formula.objects.create(
            name='关联测试公式',
            notation="R U",
            category=self.category
        )
        self.tag = FormulaTag.objects.create(name='测试标签')

    def test_create_relation_success(self):
        """测试创建关联成功"""
        relation = FormulaTagRelation.objects.create(
            formula=self.formula,
            tag=self.tag
        )

        self.assertEqual(relation.formula, self.formula)
        self.assertEqual(relation.tag, self.tag)

    def test_relation_uniqueness(self):
        """测试同一公式不能重复关联同一标签"""
        FormulaTagRelation.objects.create(formula=self.formula, tag=self.tag)

        with self.assertRaises(IntegrityError):
            FormulaTagRelation.objects.create(formula=self.formula, tag=self.tag)

    def test_formula_tags_relation(self):
        """测试公式与标签的多对多关系"""
        tag2 = FormulaTag.objects.create(name='第二个标签')

        FormulaTagRelation.objects.create(formula=self.formula, tag=self.tag)
        FormulaTagRelation.objects.create(formula=self.formula, tag=tag2)

        self.assertEqual(self.formula.tag_relations.count(), 2)
        self.assertIn(self.tag, self.formula.tag_relations.values_list('tag', flat=True))


class FormulaCollectionModelTest(TestCase):
    """公式收藏模型测试"""

    def setUp(self):
        """创建测试数据"""
        self.user = User.objects.create_user(
            email='collector@example.com',
            password='testpass',
            username='collector'
        )
        self.category = CubeCategory.objects.create(
            order=3, method='CFOP', phase='OLL', name='收藏测试分类'
        )
        self.formula = Formula.objects.create(
            name='收藏测试公式',
            notation="R U R' U'",
            category=self.category
        )

    def test_create_collection_success(self):
        """测试创建收藏成功"""
        collection = FormulaCollection.objects.create(
            user=self.user,
            formula=self.formula
        )

        self.assertEqual(collection.user, self.user)
        self.assertEqual(collection.formula, self.formula)

    def test_collection_uniqueness(self):
        """测试同一用户不能重复收藏同一公式"""
        FormulaCollection.objects.create(user=self.user, formula=self.formula)

        with self.assertRaises(IntegrityError):
            FormulaCollection.objects.create(user=self.user, formula=self.formula)

    def test_multiple_collections(self):
        """测试收藏多个公式"""
        formula2 = Formula.objects.create(
            name='第二个公式',
            notation="F R",
            category=self.category
        )

        FormulaCollection.objects.create(user=self.user, formula=self.formula)
        FormulaCollection.objects.create(user=self.user, formula=formula2)

        self.assertEqual(self.user.formula_collections.count(), 2)

    def test_get_or_create_idempotent(self):
        """测试 get_or_create 实现幂等性"""
        collection1, created1 = FormulaCollection.objects.get_or_create(
            user=self.user, formula=self.formula
        )
        self.assertTrue(created1)

        collection2, created2 = FormulaCollection.objects.get_or_create(
            user=self.user, formula=self.formula
        )
        self.assertFalse(created2)
        self.assertEqual(collection1.id, collection2.id)
