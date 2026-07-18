import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cube_api.settings.dev')

import django
django.setup()

from apps.formula.models import Formula

f2l_formulas = Formula.objects.filter(category__phase='F2L')
oll_formulas = Formula.objects.filter(category__phase='OLL')
pll_formulas = Formula.objects.filter(category__phase='PLL')

print(f'更新前：')
print(f'  F2L: {f2l_formulas.count()}个，难度分布: {set(f2l_formulas.values_list("difficulty", flat=True))}')
print(f'  OLL: {oll_formulas.count()}个，难度分布: {set(oll_formulas.values_list("difficulty", flat=True))}')
print(f'  PLL: {pll_formulas.count()}个，难度分布: {set(pll_formulas.values_list("difficulty", flat=True))}')

f2l_formulas.update(difficulty=2)
oll_formulas.update(difficulty=3)
pll_formulas.update(difficulty=4)

print(f'\n更新后：')
print(f'  F2L: {f2l_formulas.count()}个，难度统一设为2（基础）')
print(f'  OLL: {oll_formulas.count()}个，难度统一设为3（进阶）')
print(f'  PLL: {pll_formulas.count()}个，难度统一设为4（困难）')

print('\n难度映射：')
print('  基础：难度1-2（F2L）')
print('  进阶：难度3（OLL）')
print('  困难：难度4-5（PLL）')