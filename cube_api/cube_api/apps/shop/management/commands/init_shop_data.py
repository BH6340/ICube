from django.core.management.base import BaseCommand
from apps.shop.models import ProductCategory, Product


class Command(BaseCommand):
    help = 'Initialize shop data with categories and sample products'

    def handle(self, *args, **options):
        self.stdout.write('Initializing shop categories...')
        categories = [
            {'name': '三阶魔方', 'parent': None, 'sort_order': 1},
            {'name': '四阶魔方', 'parent': None, 'sort_order': 2},
            {'name': '五阶及以上', 'parent': None, 'sort_order': 3},
            {'name': '异形魔方', 'parent': None, 'sort_order': 4},
            {'name': '魔方配件', 'parent': None, 'sort_order': 5},
            {'name': '比赛专用', 'parent': None, 'sort_order': 6},
        ]

        category_map = {}
        for cat_data in categories:
            cat, _ = ProductCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'sort_order': cat_data['sort_order']
                }
            )
            category_map[cat_data['name']] = cat
            self.stdout.write(f'Created category: {cat.name}')

        self.stdout.write('Initializing sample products...')
        products = [
            {
                'name': '三阶速拧魔方',
                'description': '专业级三阶魔方，顺滑手感，适合速拧练习和比赛',
                'price': 49.90,
                'original_price': 69.90,
                'stock': 100,
                'sales_count': 256,
                'category': '三阶魔方',
                'specs': {'颜色': ['白色', '黑色'], '版本': ['标准版', '升级版']},
                'images': [],
            },
            {
                'name': '三阶磁力魔方',
                'description': '内置磁力定位系统，转体定位精准，提升还原速度',
                'price': 89.90,
                'original_price': 119.90,
                'stock': 80,
                'sales_count': 134,
                'category': '三阶魔方',
                'specs': {'颜色': ['白色', '黑色']},
                'images': [],
            },
            {
                'name': '三阶初学者套装',
                'description': '适合新手入门的三阶魔方套装，包含教程和配件',
                'price': 29.90,
                'original_price': 39.90,
                'stock': 150,
                'sales_count': 567,
                'category': '三阶魔方',
                'specs': {'颜色': ['白色']},
                'images': [],
            },
            {
                'name': '四阶魔方',
                'description': '经典四阶魔方，结构稳定，适合进阶玩家',
                'price': 79.90,
                'original_price': 99.90,
                'stock': 60,
                'sales_count': 89,
                'category': '四阶魔方',
                'specs': {'颜色': ['白色', '黑色']},
                'images': [],
            },
            {
                'name': '四阶磁力魔方',
                'description': '四阶磁力版本，手感顺滑，定位精准',
                'price': 129.90,
                'original_price': 159.90,
                'stock': 40,
                'sales_count': 56,
                'category': '四阶魔方',
                'specs': {'颜色': ['黑色']},
                'images': [],
            },
            {
                'name': '五阶魔方',
                'description': '五阶高阶魔方，挑战你的极限',
                'price': 109.90,
                'original_price': 139.90,
                'stock': 50,
                'sales_count': 45,
                'category': '五阶及以上',
                'specs': {'颜色': ['白色', '黑色']},
                'images': [],
            },
            {
                'name': '金字塔魔方',
                'description': '经典异形魔方，四面体结构，锻炼空间思维',
                'price': 39.90,
                'original_price': 49.90,
                'stock': 70,
                'sales_count': 123,
                'category': '异形魔方',
                'specs': {'颜色': ['白色', '黑色']},
                'images': [],
            },
            {
                'name': '斜转魔方',
                'description': '斜转异形魔方，独特的转动方式，趣味性强',
                'price': 44.90,
                'original_price': 59.90,
                'stock': 65,
                'sales_count': 78,
                'category': '异形魔方',
                'specs': {'颜色': ['白色']},
                'images': [],
            },
            {
                'name': '魔方底座',
                'description': '亚克力材质，透明美观，展示你的魔方收藏',
                'price': 15.90,
                'original_price': 19.90,
                'stock': 200,
                'sales_count': 345,
                'category': '魔方配件',
                'specs': {'颜色': ['透明', '黑色']},
                'images': [],
            },
            {
                'name': '魔方润滑油',
                'description': '专业魔方硅油，提升顺滑度，延长魔方寿命',
                'price': 12.90,
                'original_price': 16.90,
                'stock': 180,
                'sales_count': 289,
                'category': '魔方配件',
                'specs': {'规格': ['10ml', '30ml']},
                'images': [],
            },
            {
                'name': '魔方贴纸套装',
                'description': '高品质PVC贴纸，多种配色可选，更换方便',
                'price': 9.90,
                'original_price': 12.90,
                'stock': 120,
                'sales_count': 178,
                'category': '魔方配件',
                'specs': {'类型': ['三阶', '四阶', '五阶']},
                'images': [],
            },
            {
                'name': '比赛专用魔方',
                'description': 'WCA认证比赛用魔方，极致性能，专为竞技设计',
                'price': 159.90,
                'original_price': 199.90,
                'stock': 30,
                'sales_count': 23,
                'category': '比赛专用',
                'specs': {'颜色': ['黑色']},
                'images': [],
            },
        ]

        for prod_data in products:
            category = category_map.get(prod_data['category'])
            if not category:
                self.stderr.write(f'Category not found: {prod_data["category"]}')
                continue

            Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'description': prod_data['description'],
                    'price': prod_data['price'],
                    'original_price': prod_data['original_price'],
                    'stock': prod_data['stock'],
                    'sales_count': prod_data['sales_count'],
                    'category': category,
                    'specs': prod_data['specs'],
                    'images': prod_data['images'],
                    'is_on_sale': True,
                }
            )
            self.stdout.write(f'Created product: {prod_data["name"]}')

        self.stdout.write(self.style.SUCCESS('Shop data initialization completed!'))