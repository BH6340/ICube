import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cube_api.settings.dev')

import django
django.setup()

from apps.formula.models import Formula

phases = ['F2L', 'OLL', 'PLL']

for phase in phases:
    formulas = Formula.objects.filter(category__phase=phase).order_by('id')
    count = formulas.count()
    print(f'{phase}: {count} 个公式')
    
    for idx, formula in enumerate(formulas, start=1):
        old_name = formula.name
        new_name = f'{phase}-{idx}'
        formula.name = new_name
        formula.save()
        print(f'  {idx}: {old_name} -> {new_name}')

print('\n重命名完成！')