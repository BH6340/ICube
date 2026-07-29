# -*- coding: utf-8 -*-
"""
Formula 模块服务层测试

测试 formula 模块的服务层逻辑，包括：
    - FormulaService: 逆公式生成
    - CubeStateService: 魔方状态验证
    - FormulaMatchService: 公式匹配
"""
from django.test import TestCase

from apps.formula.services import FormulaService, CubeStateService, FormulaMatchService


class FormulaServiceTest(TestCase):
    """公式记号处理服务测试"""

    def test_generate_inverse_simple(self):
        """测试简单公式逆运算"""
        result = FormulaService.generate_inverse_notation("R U")
        self.assertEqual(result, "U' R'")

    def test_generate_inverse_double(self):
        """测试 180 度旋转的逆运算（保持不变）"""
        result = FormulaService.generate_inverse_notation("R2")
        self.assertEqual(result, "R2")

    def test_generate_inverse_complex(self):
        """测试复杂公式的逆运算"""
        result = FormulaService.generate_inverse_notation("R U R' U'")
        self.assertEqual(result, "U' R' U R")

    def test_generate_inverse_single_step(self):
        """测试单步操作的逆运算"""
        result = FormulaService.generate_inverse_notation("R")
        self.assertEqual(result, "R'")

    def test_generate_inverse_inverse_step(self):
        """测试逆向操作的逆运算"""
        result = FormulaService.generate_inverse_notation("R'")
        self.assertEqual(result, "R")

    def test_generate_inverse_layer_moves(self):
        """测试中层转动的逆运算"""
        result = FormulaService.generate_inverse_notation("M E S")
        self.assertEqual(result, "S' E' M'")

    def test_generate_inverse_whole_cube_rotation(self):
        """测试整体转动的逆运算"""
        result = FormulaService.generate_inverse_notation("x y z")
        self.assertEqual(result, "z' y' x'")

    def test_generate_inverse_double_layer_moves(self):
        """测试双层转动的逆运算"""
        result = FormulaService.generate_inverse_notation("r l u d f b")
        self.assertEqual(result, "b' f' d' u' l' r'")

    def test_generate_inverse_mixed_moves(self):
        """测试混合操作的逆运算"""
        result = FormulaService.generate_inverse_notation("R U R' U' F R U")
        self.assertEqual(result, "U' R' F' U' R' U' R")

    def test_generate_inverse_empty_string(self):
        """测试空字符串（边界情况）"""
        result = FormulaService.generate_inverse_notation("")
        self.assertEqual(result, "")

    def test_generate_inverse_with_multiple_spaces(self):
        """测试多空格分隔（边界情况）"""
        result = FormulaService.generate_inverse_notation("R  U   F")
        self.assertEqual(result, "F' U' R'")

    def test_inverse_double_inverse_returns_original(self):
        """测试逆公式的逆公式返回原公式"""
        original = "R U R' U'"
        inverse = FormulaService.generate_inverse_notation(original)
        double_inverse = FormulaService.generate_inverse_notation(inverse)
        self.assertEqual(double_inverse, original)


class CubeStateServiceTest(TestCase):
    """魔方状态验证服务测试"""

    def setUp(self):
        """准备有效的状态定义"""
        self.valid_state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
                {'pos': [1, 1, 0], 'faces': {'U': 'Y', 'R': 'R', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
                {'pos': [-1, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': 'O', 'B': '-'}},
            ]
        }

    def test_validate_valid_state(self):
        """测试验证有效的状态定义"""
        errors = CubeStateService.validate_state_definition(self.valid_state)
        self.assertEqual(errors, [])

    def test_validate_not_dict(self):
        """测试非字典类型"""
        errors = CubeStateService.validate_state_definition("not a dict")
        self.assertGreater(len(errors), 0)
        self.assertIn("必须是字典格式", errors[0])

    def test_validate_missing_order(self):
        """测试缺少 order 字段"""
        state = {'blocks': []}
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('order' in e for e in errors))

    def test_validate_invalid_order(self):
        """测试 order 字段无效"""
        state = {'order': 'invalid', 'blocks': []}
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('order' in e for e in errors))

    def test_validate_order_too_small(self):
        """测试阶数太小"""
        state = {'order': 1, 'blocks': []}
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('order' in e for e in errors))

    def test_validate_missing_blocks(self):
        """测试缺少 blocks 字段"""
        state = {'order': 3}
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('blocks' in e for e in errors))

    def test_validate_blocks_not_list(self):
        """测试 blocks 不是列表"""
        state = {'order': 3, 'blocks': 'not a list'}
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('blocks' in e for e in errors))

    def test_validate_wrong_block_count(self):
        """测试块数量不正确"""
        state = {'order': 3, 'blocks': [{'pos': [0, 1, 0], 'faces': {}}]}
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('数量' in e for e in errors))

    def test_validate_invalid_block_format(self):
        """测试块格式无效"""
        state = {
            'order': 3,
            'blocks': [
                'not a dict',  # 无效格式
            ] + [
                {'pos': [i, j, k], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}}
                for i in [-1, 0, 1]
                for j in [-1, 0, 1]
                for k in [-1, 0, 1]
            ][:27]
        }
        # 调整 blocks 数量为 27
        state['blocks'] = state['blocks'][:27]
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('字典格式' in e for e in errors))

    def test_validate_invalid_pos_format(self):
        """测试位置格式无效"""
        state = {
            'order': 3,
            'blocks': [
                {'pos': 'invalid', 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
            ] + [
                {'pos': [i, j, k], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}}
                for i in [-1, 0, 1]
                for j in [-1, 0, 1]
                for k in [-1, 0, 1]
            ][:27]
        }
        state['blocks'] = state['blocks'][:27]
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('pos' in e for e in errors))

    def test_validate_missing_faces(self):
        """测试缺少面字段"""
        state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {}},
            ] + [
                {'pos': [i, j, k], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}}
                for i in [-1, 0, 1]
                for j in [-1, 0, 1]
                for k in [-1, 0, 1]
            ][:27]
        }
        state['blocks'] = state['blocks'][:27]
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('faces' in e or 'U' in e for e in errors))

    def test_validate_invalid_color(self):
        """测试无效颜色值"""
        state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'X', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
            ] + [
                {'pos': [i, j, k], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}}
                for i in [-1, 0, 1]
                for j in [-1, 0, 1]
                for k in [-1, 0, 1]
            ][:27]
        }
        state['blocks'] = state['blocks'][:27]
        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('颜色' in e for e in errors))

    def test_validate_all_center_colors_correct(self):
        """测试所有中心块颜色正确"""
        state = {
            'order': 3,
            'blocks': [
                # 中心块
                {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},  # 上
                {'pos': [0, -1, 0], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': 'W', 'L': '-', 'B': '-'}},  # 下
                {'pos': [0, 0, 1], 'faces': {'U': '-', 'R': '-', 'F': 'B', 'D': '-', 'L': '-', 'B': '-'}},  # 前
                {'pos': [0, 0, -1], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': 'G'}},  # 后
                {'pos': [-1, 0, 0], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': 'O', 'B': '-'}},  # 左
                {'pos': [1, 0, 0], 'faces': {'U': '-', 'R': 'R', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},  # 右
            ] + [
                {'pos': [i, j, k], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}}
                for i in [-1, 0, 1]
                for j in [-1, 0, 1]
                for k in [-1, 0, 1]
                if (i, j, k) not in [(0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (-1, 0, 0), (1, 0, 0)]
            ]
        }
        # 确保有 27 个块
        while len(state['blocks']) < 27:
            state['blocks'].append({'pos': [0, 0, 0], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}})
        state['blocks'] = state['blocks'][:27]

        errors = CubeStateService.validate_state_definition(state)
        self.assertEqual(errors, [])

    def test_validate_wrong_center_color(self):
        """测试中心块颜色错误"""
        state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'R', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},  # 上中心应为 Y
            ] + [
                {'pos': [i, j, k], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}}
                for i in [-1, 0, 1]
                for j in [-1, 0, 1]
                for k in [-1, 0, 1]
                if (i, j, k) != (0, 1, 0)
            ]
        }
        while len(state['blocks']) < 27:
            state['blocks'].append({'pos': [0, 0, 0], 'faces': {'U': '-', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}})
        state['blocks'] = state['blocks'][:27]

        errors = CubeStateService.validate_state_definition(state)
        self.assertTrue(any('中心块' in e for e in errors))


class FormulaMatchServiceTest(TestCase):
    """公式匹配服务测试"""

    def setUp(self):
        """创建测试数据"""
        from apps.formula.models import CubeCategory, CubeState, Formula

        self.category = CubeCategory.objects.create(
            order=3, method='CFOP', phase='OLL', name='匹配测试分类'
        )
        self.state = CubeState.objects.create(
            name='匹配测试状态',
            state_definition={
                'order': 3,
                'blocks': [
                    {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
                ]
            },
            category=self.category
        )

    def test_match_formulas_empty_state(self):
        """测试空状态匹配（无匹配公式）"""
        user_state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
            ]
        }
        result = FormulaMatchService.match_formulas(user_state)
        self.assertIsInstance(result, list)

    def test_match_formulas_with_pre_state(self):
        """测试有前置状态的公式匹配"""
        from apps.formula.models import Formula

        pre_state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': 'R', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
            ]
        }

        # 创建有前置状态的公式
        Formula.objects.create(
            name='匹配公式',
            notation="R U",
            category=self.category,
            pre_state_definition=pre_state
        )

        # 用户状态匹配前置状态
        user_state = pre_state.copy()
        result = FormulaMatchService.match_formulas(user_state)
        self.assertGreater(len(result), 0)

    def test_match_state_match_partial(self):
        """测试部分匹配（'-' 不关心的面）"""
        formula_state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
            ]
        }
        user_state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': 'R', 'F': 'B', 'D': '-', 'L': '-', 'B': '-'}},
            ]
        }

        # 公式中 R 面为 '-'（不关心），用户状态 R 面为 'R'，应该匹配
        result = FormulaMatchService._is_state_match(user_state, formula_state)
        self.assertTrue(result)

    def test_match_state_mismatch(self):
        """测试不匹配的状态"""
        formula_state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'R', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
            ]
        }
        user_state = {
            'order': 3,
            'blocks': [
                {'pos': [0, 1, 0], 'faces': {'U': 'Y', 'R': '-', 'F': '-', 'D': '-', 'L': '-', 'B': '-'}},
            ]
        }

        # 公式中 U 面为 'R'，用户状态 U 面为 'Y'，不匹配
        result = FormulaMatchService._is_state_match(user_state, formula_state)
        self.assertFalse(result)
