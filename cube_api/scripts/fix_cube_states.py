import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cube_api.settings.dev')

import django
django.setup()

from apps.formula.models import CubeState

def fix_f2l_state():
    try:
        state = CubeState.objects.get(name='F2L完成状态')
        state.state_definition = {
            'faces': {
                'U': [['gray', 'gray', 'gray'], ['gray', 'gray', 'gray'], ['gray', 'gray', 'gray']],
                'D': [['white', 'white', 'white'], ['white', 'white', 'white'], ['white', 'white', 'white']],
                'F': [['gray', 'gray', 'gray'], ['blue', 'blue', 'blue'], ['blue', 'blue', 'blue']],
                'B': [['gray', 'gray', 'gray'], ['green', 'green', 'green'], ['green', 'green', 'green']],
                'L': [['gray', 'gray', 'gray'], ['orange', 'orange', 'orange'], ['orange', 'orange', 'orange']],
                'R': [['gray', 'gray', 'gray'], ['red', 'red', 'red'], ['red', 'red', 'red']],
            },
            'description': '底层和前两层已完成，第三层和顶面为灰色'
        }
        state.save()
        print('F2L完成状态已修复')
    except CubeState.DoesNotExist:
        print('F2L完成状态不存在')

def fix_oll_state():
    try:
        state = CubeState.objects.get(name='OLL完成状态')
        state.state_definition = {
            'faces': {
                'U': [['yellow', 'yellow', 'yellow'], ['yellow', 'yellow', 'yellow'], ['yellow', 'yellow', 'yellow']],
                'D': [['white', 'white', 'white'], ['white', 'white', 'white'], ['white', 'white', 'white']],
                'F': [['yellow', 'blue', 'blue'], ['yellow', 'blue', 'blue'], ['yellow', 'orange', 'red']],
                'B': [['yellow', 'green', 'green'], ['yellow', 'green', 'green'], ['yellow', 'red', 'orange']],
                'L': [['yellow', 'orange', 'orange'], ['yellow', 'orange', 'orange'], ['yellow', 'green', 'blue']],
                'R': [['yellow', 'red', 'red'], ['yellow', 'red', 'red'], ['yellow', 'blue', 'green']],
            },
            'description': '底层、前两层、顶面方向已完成，角块位置待调整'
        }
        state.save()
        print('OLL完成状态已修复')
    except CubeState.DoesNotExist:
        print('OLL完成状态不存在')

def fix_pll_state():
    try:
        state = CubeState.objects.get(name='PLL完成状态')
        state.state_definition = {
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
        state.save()
        print('PLL完成状态已修复')
    except CubeState.DoesNotExist:
        print('PLL完成状态不存在')

if __name__ == '__main__':
    fix_f2l_state()
    fix_oll_state()
    fix_pll_state()
    print('所有状态已修复')