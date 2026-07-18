import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cube_api.settings.dev')

import django
django.setup()

from apps.formula.models import Formula

def count_steps(notation):
    if not notation:
        return 0
    steps = notation.split()
    return len(steps)

print('按公式步数更新难度等级：')
print('  6步及以内：基础（level=1）')
print('  7-11步：进阶（level=2）')
print('  12步及以上：困难（level=3）')
print()

formulas = Formula.objects.all()
stats = {1: 0, 2: 0, 3: 0}

for formula in formulas:
    steps = count_steps(formula.notation)
    if steps <= 6:
        level = 1
    elif steps <= 11:
        level = 2
    else:
        level = 3
    
    formula.difficulty = level
    formula.save()
    stats[level] += 1

print('更新完成！')
print(f'  基础（level=1）：{stats[1]}个公式')
print(f'  进阶（level=2）：{stats[2]}个公式')
print(f'  困难（level=3）：{stats[3]}个公式')
print(f'  总计：{formulas.count()}个公式')