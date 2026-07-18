from django.core.management.base import BaseCommand
from apps.formula.models import CubeState, CubeCategory, Formula


class Command(BaseCommand):
    help = '插入F2L、OLL、PLL的状态定义并更新公式的目标状态'

    def handle(self, *args, **options):
        self.stdout.write('开始插入魔方状态定义...')

        categories = {
            'F2L': CubeCategory.objects.get(method='CFOP', phase='F2L'),
            'OLL': CubeCategory.objects.get(method='CFOP', phase='OLL'),
            'PLL': CubeCategory.objects.get(method='CFOP', phase='PLL'),
        }

        f2l_state = self.create_f2l_state(categories['F2L'])
        oll_state = self.create_oll_state(categories['OLL'])
        pll_state = self.create_pll_state(categories['PLL'])

        self.update_formula_target_states(categories['F2L'], f2l_state)
        self.update_formula_target_states(categories['OLL'], oll_state)
        self.update_formula_target_states(categories['PLL'], pll_state)

        self.stdout.write(self.style.SUCCESS('状态定义插入完成！'))

    def create_f2l_state(self, category):
        state, created = CubeState.objects.get_or_create(
            name='F2L完成状态',
            defaults={
                'state_definition': self.get_f2l_state_definition(),
                'description': '底层和前两层已完成，顶层和第三层为灰色（未完成状态）',
                'category': category,
            }
        )
        if created:
            self.stdout.write(f'创建状态: {state.name}')
        else:
            self.stdout.write(f'状态已存在: {state.name}')
        return state

    def create_oll_state(self, category):
        state, created = CubeState.objects.get_or_create(
            name='OLL完成状态',
            defaults={
                'state_definition': self.get_oll_state_definition(),
                'description': '底层、前两层、顶面方向已完成，角块位置可能不正确',
                'category': category,
            }
        )
        if created:
            self.stdout.write(f'创建状态: {state.name}')
        else:
            self.stdout.write(f'状态已存在: {state.name}')
        return state

    def create_pll_state(self, category):
        state, created = CubeState.objects.get_or_create(
            name='PLL完成状态',
            defaults={
                'state_definition': self.get_pll_state_definition(),
                'description': '完全还原的魔方状态',
                'category': category,
            }
        )
        if created:
            self.stdout.write(f'创建状态: {state.name}')
        else:
            self.stdout.write(f'状态已存在: {state.name}')
        return state

    def update_formula_target_states(self, category, state):
        count = Formula.objects.filter(category=category).update(target_state=state)
        self.stdout.write(f'更新 {category.phase} 公式目标状态: {count} 条')

    def get_f2l_state_definition(self):
        return {
            'faces': {
                'U': [['gray', 'gray', 'gray'], ['gray', 'gray', 'gray'], ['gray', 'gray', 'gray']],
                'D': [['white', 'white', 'white'], ['white', 'white', 'white'], ['white', 'white', 'white']],
                'F': [['blue', 'blue', 'gray'], ['blue', 'blue', 'gray'], ['gray', 'gray', 'gray']],
                'B': [['green', 'green', 'gray'], ['green', 'green', 'gray'], ['gray', 'gray', 'gray']],
                'L': [['orange', 'orange', 'gray'], ['orange', 'orange', 'gray'], ['gray', 'gray', 'gray']],
                'R': [['red', 'red', 'gray'], ['red', 'red', 'gray'], ['gray', 'gray', 'gray']],
            },
            'description': '底层和前两层已完成，第三层和顶面为灰色'
        }

    def get_oll_state_definition(self):
        return {
            'faces': {
                'U': [['yellow', 'yellow', 'yellow'], ['yellow', 'yellow', 'yellow'], ['yellow', 'yellow', 'yellow']],
                'D': [['white', 'white', 'white'], ['white', 'white', 'white'], ['white', 'white', 'white']],
                'F': [['blue', 'blue', 'yellow'], ['blue', 'blue', 'yellow'], ['orange', 'red', 'yellow']],
                'B': [['green', 'green', 'yellow'], ['green', 'green', 'yellow'], ['red', 'orange', 'yellow']],
                'L': [['orange', 'orange', 'yellow'], ['orange', 'orange', 'yellow'], ['green', 'blue', 'yellow']],
                'R': [['red', 'red', 'yellow'], ['red', 'red', 'yellow'], ['blue', 'green', 'yellow']],
            },
            'description': '底层、前两层、顶面方向已完成，角块位置待调整'
        }

    def get_pll_state_definition(self):
        return {
            'faces': {
                'U': [['yellow', 'yellow', 'yellow'], ['yellow', 'yellow', 'yellow'], ['yellow', 'yellow', 'yellow']],
                'D': [['white', 'white', 'white'], ['white', 'white', 'white'], ['white', 'white', 'white']],
                'F': [['blue', 'blue', 'blue'], ['blue', 'blue', 'blue'], ['blue', 'blue', 'blue']],
                'B': [['green', 'green', 'green'], ['green', 'green', 'green'], ['green', 'green', 'green']],
                'L': [['orange', 'orange', 'orange'], ['orange', 'orange', 'orange'], ['orange', 'orange', 'orange']],
                'R': [['red', 'red', 'red'], ['red', 'red', 'red'], ['red', 'red', 'red']],
            },
            'description': '完全还原的魔方状态'
        }