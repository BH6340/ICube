import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cube_api.settings.dev')

import django
django.setup()

from apps.formula.models import Formula
from apps.formula.services import FormulaService

updated = 0
for f in Formula.objects.all():
    f.inverse_notation = FormulaService.generate_inverse_notation(f.notation)
    f.save()
    updated += 1

print(f'更新 {updated} 个公式')

f = Formula.objects.first()
print(f'示例: {f.name}')
print(f'记号: {f.notation}')
print(f'逆公式: {f.inverse_notation}')