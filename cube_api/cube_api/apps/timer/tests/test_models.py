# -*- coding: utf-8 -*-
"""
Timer 模块测试

测试计时器模块的核心功能，包括：
    - 计时记录创建与状态管理
    - 计时记录查询
    - 魔方类型与还原方法
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.timer.models import TimerRecord

User = get_user_model()


class TimerRecordModelTest(TestCase):
    """计时记录模型测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='timer@example.com',
            password='testpass',
            username='timeruser'
        )
        self.record = TimerRecord.objects.create(
            user=self.user,
            cube_type='3x3',
            method='cfop',
            time_ms=15432,
            scramble="R U R' U'"
        )

    def test_create_record_success(self):
        """测试创建计时记录"""
        self.assertEqual(self.record.user, self.user)
        self.assertEqual(self.record.cube_type, '3x3')
        self.assertEqual(self.record.method, 'cfop')
        self.assertEqual(self.record.time_ms, 15432)
        self.assertEqual(self.record.scramble, "R U R' U'")

    def test_record_str_method(self):
        """测试 __str__ 方法"""
        self.assertEqual(str(self.record), 'timeruser - 3x3 - 15432ms')

    def test_record_default_values(self):
        """测试默认值"""
        record = TimerRecord.objects.create(
            user=self.user,
            time_ms=10000
        )
        self.assertEqual(record.cube_type, '3x3')
        self.assertEqual(record.method, 'layer')
        self.assertEqual(record.scramble, '')

    def test_record_cube_type_choices(self):
        """测试魔方类型枚举"""
        valid_types = [choice[0] for choice in TimerRecord.CUBE_TYPE_CHOICES]
        self.assertIn('2x2', valid_types)
        self.assertIn('3x3', valid_types)
        self.assertIn('4x4', valid_types)
        self.assertIn('5x5', valid_types)
        self.assertIn('other', valid_types)

    def test_record_method_choices(self):
        """测试还原方法枚举"""
        valid_methods = [choice[0] for choice in TimerRecord.METHOD_CHOICES]
        self.assertIn('layer', valid_methods)
        self.assertIn('cfop', valid_methods)
        self.assertIn('roux', valid_methods)
        self.assertIn('zbll', valid_methods)
        self.assertIn('other', valid_methods)

    def test_record_ordering(self):
        """测试记录排序（按创建时间倒序）"""
        record1 = TimerRecord.objects.create(user=self.user, time_ms=10000)
        record2 = TimerRecord.objects.create(user=self.user, time_ms=20000)

        records = TimerRecord.objects.filter(user=self.user)
        self.assertEqual(records[0].id, record2.id)
        self.assertEqual(records[1].id, record1.id)
        self.assertEqual(records[2].id, self.record.id)

    def test_record_user_relation(self):
        """测试用户与记录的一对多关系"""
        record2 = TimerRecord.objects.create(user=self.user, time_ms=20000)
        self.assertEqual(self.user.timer_records.count(), 2)

    def test_record_with_different_cube_types(self):
        """测试不同魔方类型的记录"""
        record_2x2 = TimerRecord.objects.create(
            user=self.user, cube_type='2x2', method='layer', time_ms=8000
        )
        record_4x4 = TimerRecord.objects.create(
            user=self.user, cube_type='4x4', method='cfop', time_ms=45000
        )
        self.assertEqual(record_2x2.cube_type, '2x2')
        self.assertEqual(record_4x4.cube_type, '4x4')

    def test_record_with_different_methods(self):
        """测试不同还原方法的记录"""
        record_roux = TimerRecord.objects.create(
            user=self.user, cube_type='3x3', method='roux', time_ms=12000
        )
        record_zbll = TimerRecord.objects.create(
            user=self.user, cube_type='3x3', method='zbll', time_ms=9000
        )
        self.assertEqual(record_roux.method, 'roux')
        self.assertEqual(record_zbll.method, 'zbll')

    def test_record_time_precision(self):
        """测试毫秒级时间精度"""
        record = TimerRecord.objects.create(
            user=self.user, time_ms=12345
        )
        self.assertEqual(record.time_ms, 12345)

    def test_record_scramble_optional(self):
        """测试打乱公式可选"""
        record = TimerRecord.objects.create(
            user=self.user, time_ms=10000
        )
        self.assertEqual(record.scramble, '')
