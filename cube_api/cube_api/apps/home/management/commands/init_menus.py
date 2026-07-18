# apps/home/management/commands/init_menus.py
from django.core.management.base import BaseCommand
# 🌟 注意这里：修改为从 home 引入模型
from apps.home.models import NavigationMenu


class Command(BaseCommand):
    help = '一键初始化/重置系统导航栏数据'

    def handle(self, *args, **options):
        NavigationMenu.objects.all().delete()

        main_menus = [
            {"index": "1", "label": "首页", "path": "/", "category": "main", "sort_order": 10,
             "match_paths": ["/home"]},
            {"index": "2", "label": "教程", "path": "/tutorials", "category": "main", "sort_order": 20,
             "match_paths": ["/tutorials"]},
            {"index": "3", "label": "公式库", "path": "/formulas", "category": "main", "sort_order": 30,
             "match_paths": ["/formulas"]},
            {"index": "4", "label": "计时器", "path": "/timer", "category": "main", "sort_order": 40,
             "match_paths": ["/timer"]},
            {"index": "5", "label": "交流论坛", "path": "/forum", "category": "main", "sort_order": 50,
             "match_paths": ["/forum"]},
            {"index": "6", "label": "魔方商店", "path": "/shop", "category": "main", "sort_order": 60,
             "match_paths": ["/shop"]},
        ]

        profile_menus = [
            {"index": "p-1", "label": "返回首页", "path": "/", "category": "profile", "sort_order": 10,
             "match_paths": []},
            {"index": "p-2", "label": "个人信息", "path": "/profiles/info", "category": "profile", "sort_order": 20,
             "match_paths": ["/profiles/info"]},
            {"index": "p-3", "label": "公式收藏", "path": "/profiles/collections", "category": "profile",
             "sort_order": 30, "match_paths": ["/profiles/collections"]},
            {"index": "p-4", "label": "我的数据", "path": "/profiles/datas", "category": "profile", "sort_order": 40,
             "match_paths": ["/profiles/datas"]},
            {"index": "p-5", "label": "我的帖子", "path": "/profiles/posts", "category": "profile", "sort_order": 50,
             "match_paths": ["/profiles/posts"]},
        ]

        menu_instances = [NavigationMenu(**menu) for menu in (main_menus + profile_menus)]
        NavigationMenu.objects.bulk_create(menu_instances)
        self.stdout.write(self.style.SUCCESS('🎉 [Home App] 导航栏数据批量插入成功！'))