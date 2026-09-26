"""
Timer 缓存服务测试
"""

from apps.timer.services import TimerStatsCacheService
from django.core.cache import cache
from django.test import TestCase, override_settings


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    }
)
class TimerStatsCacheServiceTest(TestCase):
    """TimerStatsCacheService 单元测试"""

    def setUp(self):
        cache.clear()

    def test_set_and_get_today_records(self):
        """测试设置和获取今日记录缓存"""
        records = [{"id": 1, "time_ms": 10000}]
        TimerStatsCacheService.set_today_records(1, "3x3", "cfop", records)
        result = TimerStatsCacheService.get_today_records(1, "3x3", "cfop")
        self.assertEqual(result, records)

    def test_get_today_records_not_exist(self):
        """测试缓存不存在时返回 None"""
        result = TimerStatsCacheService.get_today_records(999, "3x3", "cfop")
        self.assertIsNone(result)

    def test_set_and_get_today_stats(self):
        """测试设置和获取今日统计缓存"""
        stats = {"total_count": 5, "best_time": 8000}
        TimerStatsCacheService.set_today_stats(1, "3x3", "cfop", stats)
        result = TimerStatsCacheService.get_today_stats(1, "3x3", "cfop")
        self.assertEqual(result, stats)

    def test_invalidate_user_cache(self):
        """测试失效用户所有缓存"""
        TimerStatsCacheService.set_today_records(1, "3x3", "cfop", [{"id": 1}])
        TimerStatsCacheService.set_today_stats(1, "3x3", "cfop", {"total": 1})
        TimerStatsCacheService.set_today_records(1, "2x2", "layer", [{"id": 2}])

        # 另一个用户的缓存不受影响
        TimerStatsCacheService.set_today_records(2, "3x3", "cfop", [{"id": 3}])

        TimerStatsCacheService.invalidate_user_cache(1)

        self.assertIsNone(TimerStatsCacheService.get_today_records(1, "3x3", "cfop"))
        self.assertIsNone(TimerStatsCacheService.get_today_stats(1, "3x3", "cfop"))
        self.assertIsNone(TimerStatsCacheService.get_today_records(1, "2x2", "layer"))
        # 其他用户的缓存还在
        self.assertIsNotNone(TimerStatsCacheService.get_today_records(2, "3x3", "cfop"))

    def test_different_cube_type_different_cache(self):
        """测试不同 cube_type 使用不同缓存"""
        records_3x3 = [{"id": 1, "cube_type": "3x3"}]
        records_2x2 = [{"id": 2, "cube_type": "2x2"}]
        TimerStatsCacheService.set_today_records(1, "3x3", "cfop", records_3x3)
        TimerStatsCacheService.set_today_records(1, "2x2", "cfop", records_2x2)

        self.assertEqual(
            TimerStatsCacheService.get_today_records(1, "3x3", "cfop"),
            records_3x3,
        )
        self.assertEqual(
            TimerStatsCacheService.get_today_records(1, "2x2", "cfop"),
            records_2x2,
        )

    def test_different_method_different_cache(self):
        """测试不同 method 使用不同缓存"""
        records_cfop = [{"id": 1, "method": "cfop"}]
        records_layer = [{"id": 2, "method": "layer"}]
        TimerStatsCacheService.set_today_records(1, "3x3", "cfop", records_cfop)
        TimerStatsCacheService.set_today_records(1, "3x3", "layer", records_layer)

        self.assertEqual(
            TimerStatsCacheService.get_today_records(1, "3x3", "cfop"),
            records_cfop,
        )
        self.assertEqual(
            TimerStatsCacheService.get_today_records(1, "3x3", "layer"),
            records_layer,
        )
