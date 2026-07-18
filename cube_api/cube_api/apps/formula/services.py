class FormulaService:
    NOTATION_INVERSE_MAP = {
        'R': "R'", 'R\'': 'R', 'R2': 'R2',
        'L': "L'", 'L\'': 'L', 'L2': 'L2',
        'U': "U'", 'U\'': 'U', 'U2': 'U2',
        'D': "D'", 'D\'': 'D', 'D2': 'D2',
        'F': "F'", 'F\'': 'F', 'F2': 'F2',
        'B': "B'", 'B\'': 'B', 'B2': 'B2',
        'M': "M'", 'M\'': 'M', 'M2': 'M2',
        'E': "E'", 'E\'': 'E', 'E2': 'E2',
        'S': "S'", 'S\'': 'S', 'S2': 'S2',
        'x': "x'", 'x\'': 'x', 'x2': 'x2',
        'y': "y'", 'y\'': 'y', 'y2': 'y2',
        'z': "z'", 'z\'': 'z', 'z2': 'z2',
        'r': "r'", 'r\'': 'r', 'r2': 'r2',
        'l': "l'", 'l\'': 'l', 'l2': 'l2',
        'u': "u'", 'u\'': 'u', 'u2': 'u2',
        'd': "d'", 'd\'': 'd', 'd2': 'd2',
        'f': "f'", 'f\'': 'f', 'f2': 'f2',
        'b': "b'", 'b\'': 'b', 'b2': 'b2',
    }

    @classmethod
    def generate_inverse_notation(cls, notation):
        steps = notation.split()
        reversed_steps = reversed(steps)
        inverse_steps = [cls.NOTATION_INVERSE_MAP.get(step, step) for step in reversed_steps]
        return ' '.join(inverse_steps)


class CubeStateService:
    CENTER_COLORS = {
        (0, 1, 0): "Y",
        (0, -1, 0): "W",
        (0, 0, 1): "B",
        (0, 0, -1): "G",
        (-1, 0, 0): "O",
        (1, 0, 0): "R",
    }

    @classmethod
    def validate_state_definition(cls, state_def):
        errors = []

        if not isinstance(state_def, dict):
            errors.append("状态定义必须是字典格式")
            return errors

        if 'order' not in state_def:
            errors.append("缺少 order 字段")
        else:
            if not isinstance(state_def['order'], int) or state_def['order'] < 2:
                errors.append("order 必须是大于等于2的整数")

        if 'blocks' not in state_def:
            errors.append("缺少 blocks 字段")
        else:
            if not isinstance(state_def['blocks'], list):
                errors.append("blocks 必须是列表格式")
            else:
                expected_blocks = state_def.get('order', 3) ** 3
                if len(state_def['blocks']) != expected_blocks:
                    errors.append(f"blocks 数量不正确，期望 {expected_blocks} 个，实际 {len(state_def['blocks'])} 个")

                for block in state_def['blocks']:
                    errors.extend(cls._validate_block(block))

                errors.extend(cls._validate_center_blocks(state_def['blocks']))
                errors.extend(cls._validate_adjacent_blocks(state_def['blocks']))

        return errors

    @classmethod
    def _validate_block(cls, block):
        errors = []

        if not isinstance(block, dict):
            errors.append("每个块必须是字典格式")
            return errors

        if 'pos' not in block:
            errors.append("缺少 pos 字段")
        else:
            pos = block['pos']
            if not isinstance(pos, (list, tuple)) or len(pos) != 3:
                errors.append("pos 必须是包含3个元素的列表或元组")
            else:
                for p in pos:
                    if not isinstance(p, int):
                        errors.append("pos 的每个元素必须是整数")

        if 'faces' not in block:
            errors.append("缺少 faces 字段")
        else:
            faces = block['faces']
            if not isinstance(faces, dict):
                errors.append("faces 必须是字典格式")
            else:
                required_faces = ['U', 'R', 'F', 'D', 'L', 'B']
                for face in required_faces:
                    if face not in faces:
                        errors.append(f"缺少 {face} 面")

                valid_colors = ['Y', 'W', 'B', 'G', 'O', 'R', '-', '?']
                for face, color in faces.items():
                    if color not in valid_colors:
                        errors.append(f"面 {face} 的颜色 {color} 无效，有效值: {', '.join(valid_colors)}")

        return errors

    @classmethod
    def _validate_center_blocks(cls, blocks):
        errors = []

        for pos, expected_color in cls.CENTER_COLORS.items():
            block = cls._find_block_by_pos(blocks, pos)
            if block:
                face_key = cls._get_center_face_key(pos)
                actual_color = block['faces'].get(face_key, '')
                if actual_color != expected_color:
                    errors.append(f"中心块 {pos} 的 {face_key} 面颜色错误，期望 {expected_color}，实际 {actual_color}")

        return errors

    @classmethod
    def _validate_adjacent_blocks(cls, blocks):
        errors = []

        for block in blocks:
            pos = tuple(block['pos']) if isinstance(block['pos'], list) else block['pos']

            for direction, neighbor_pos in cls._get_neighbors(pos):
                neighbor = cls._find_block_by_pos(blocks, neighbor_pos)
                if neighbor:
                    my_face = cls._direction_to_face(direction)
                    neighbor_face = cls._opposite_face(my_face)

                    my_color = block['faces'].get(my_face, '-')
                    neighbor_color = neighbor['faces'].get(neighbor_face, '-')

                    if my_color != '-' and neighbor_color != '-' and my_color != neighbor_color:
                        errors.append(f"块 {pos} 的 {my_face} 面与相邻块 {neighbor_pos} 的 {neighbor_face} 面颜色不一致")

        return errors

    @classmethod
    def _find_block_by_pos(cls, blocks, pos):
        pos_tuple = tuple(pos) if isinstance(pos, list) else pos
        for block in blocks:
            block_pos = tuple(block['pos']) if isinstance(block['pos'], list) else block['pos']
            if block_pos == pos_tuple:
                return block
        return None

    @classmethod
    def _get_center_face_key(cls, pos):
        if pos[1] == 1:
            return "U"
        if pos[1] == -1:
            return "D"
        if pos[2] == 1:
            return "F"
        if pos[2] == -1:
            return "B"
        if pos[0] == -1:
            return "L"
        if pos[0] == 1:
            return "R"
        return None

    @classmethod
    def _get_neighbors(cls, pos):
        deltas = {
            'R': (1, 0, 0), 'L': (-1, 0, 0),
            'U': (0, 1, 0), 'D': (0, -1, 0),
            'F': (0, 0, 1), 'B': (0, 0, -1),
        }

        neighbors = []
        order = 3
        half_order = (order - 1) // 2

        for direction, delta in deltas.items():
            neighbor_pos = (pos[0] + delta[0], pos[1] + delta[1], pos[2] + delta[2])
            if all(-half_order <= p <= half_order for p in neighbor_pos):
                neighbors.append((direction, neighbor_pos))

        return neighbors

    @classmethod
    def _direction_to_face(cls, direction):
        return direction

    @classmethod
    def _opposite_face(cls, face):
        opposites = {'U': 'D', 'D': 'U', 'F': 'B', 'B': 'F', 'L': 'R', 'R': 'L'}
        return opposites.get(face, face)


class FormulaMatchService:
    @classmethod
    def match_formulas(cls, user_state):
        from .models import Formula

        matched = []

        for formula in Formula.objects.filter(pre_state_definition__isnull=False):
            if cls._is_state_match(user_state, formula.pre_state_definition):
                matched.append(formula)

        for formula in Formula.objects.filter(
            pre_state_definition__isnull=True,
            target_state__isnull=False
        ):
            result_state = cls._execute_formula(user_state, formula.notation)
            if cls._is_state_match(result_state, formula.target_state.state_definition):
                matched.append(formula)

        return matched

    @classmethod
    def _is_state_match(cls, user_state, formula_state):
        for block in formula_state.get('blocks', []):
            pos = block['pos']
            faces = block.get('faces', {})

            user_block = cls._find_block_by_pos(user_state.get('blocks', []), pos)
            if not user_block:
                continue

            for face, color in faces.items():
                if color != '-' and user_block.get('faces', {}).get(face, '-') != color:
                    return False

        return True

    @classmethod
    def _find_block_by_pos(cls, blocks, pos):
        pos_tuple = tuple(pos) if isinstance(pos, list) else pos
        for block in blocks:
            block_pos = tuple(block['pos']) if isinstance(block['pos'], list) else block['pos']
            if block_pos == pos_tuple:
                return block
        return None

    @classmethod
    def _execute_formula(cls, state, notation):
        return state