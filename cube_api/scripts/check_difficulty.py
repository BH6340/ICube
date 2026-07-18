import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cube_api.settings.dev')

import django
django.setup()

from apps.formula.models import Formula
from django.db.models import Count

result = Formula.objects.values('difficulty').annotate(count=Count('id')).order_by('difficulty')
print('难度分布:')
for item in result:
    print(f'  难度{item["difficulty"]}: {item["count"]}个')

print(f'\n总计: {Formula.objects.count()}个')