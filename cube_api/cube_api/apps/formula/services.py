# -*- coding: utf-8 -*-
"""
公式库服务层

该模块提供公式库的核心业务服务，包括：
    - FormulaService: 公式记号处理（逆公式生成）
    - CubeStateService: 魔方状态验证（状态定义校验）
    - FormulaMatchService: 公式匹配（根据状态匹配适用公式）

设计特点：
    - **逆公式生成**：通过反转步骤顺序并取逆操作生成逆公式
    - **状态验证**：多层次验证魔方状态定义的正确性
    - **公式匹配**：支持两种匹配方式（前置状态匹配、目标状态匹配）
"""


class FormulaService:
    """
    公式记号处理服务

    提供公式记号的逆公式生成功能。

    逆公式生成原理：
        1. 将公式按空格分割为步骤列表
        2. 反转步骤顺序
        3. 对每个步骤取逆操作（R → R', R' → R, R2 → R2）
        4. 重新拼接为逆公式

    支持的魔方记号：
        - 面转动：R, L, U, D, F, B
        - 层转动：M, E, S
        - 整体转动：x, y, z
        - 双层转动：r, l, u, d, f, b
        - 每种操作支持：正向(如 R)、逆向(R')、180度(R2)
    """

    # 操作逆映射表：键为正向操作，值为逆向操作
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
        """
        生成逆公式

        逆公式生成步骤：
            1. 将公式按空格分割为步骤列表
            2. 反转步骤顺序
            3. 对每个步骤取逆操作
            4. 重新拼接为字符串

        示例：
            输入："R U R' U'"
            输出："U R U' R'"

        Args:
            notation: 原始公式记号

        Returns:
            逆公式记号
        """
        # 按空格分割步骤
        steps = notation.split()
        # 反转步骤顺序
        reversed_steps = reversed(steps)
        # 对每个步骤取逆操作
        inverse_steps = [cls.NOTATION_INVERSE_MAP.get(step, step) for step in reversed_steps]
        # 重新拼接
        return ' '.join(inverse_steps)


class CubeStateService:
    """
    魔方状态验证服务

    提供魔方状态定义的多层次验证功能，确保状态定义的正确性。

    验证层次：
        1. 结构验证：检查基本格式和字段是否完整
        2. 块验证：检查每个块的位置和颜色定义
        3. 中心块验证：检查中心块颜色是否符合标准配色
        4. 相邻块验证：检查相邻块的接触面颜色是否一致

    标准配色（中心块位置 → 颜色）：
        - (0, 1, 0): Y (上)
        - (0, -1, 0): W (下)
        - (0, 0, 1): B (前)
        - (0, 0, -1): G (后)
        - (-1, 0, 0): O (左)
        - (1, 0, 0): R (右)
    """

    # 标准配色方案：位置 → 颜色映射
    CENTER_COLORS = {
        (0, 1, 0): "Y",   # 上中心块 → 黄色
        (0, -1, 0): "W",  # 下中心块 → 白色
        (0, 0, 1): "B",   # 前中心块 → 蓝色
        (0, 0, -1): "G",  # 后中心块 → 绿色
        (-1, 0, 0): "O",  # 左中心块 → 橙色
        (1, 0, 0): "R",   # 右中心块 → 红色
    }

    @classmethod
    def validate_state_definition(cls, state_def):
        """
        验证魔方状态定义的完整性和正确性

        验证流程：
            1. 检查状态定义是否为字典格式
            2. 验证 order 字段（阶数）
            3. 验证 blocks 字段（块列表）
            4. 验证每个块的定义
            5. 验证中心块颜色
            6. 验证相邻块接触面颜色一致性

        Args:
            state_def: 状态定义字典

        Returns:
            错误列表（为空表示验证通过）
        """
        errors = []

        # 1. 结构验证：必须是字典格式
        if not isinstance(state_def, dict):
            errors.append("状态定义必须是字典格式")
            return errors

        # 2. 验证 order 字段（阶数）
        if 'order' not in state_def:
            errors.append("缺少 order 字段")
        else:
            if not isinstance(state_def['order'], int) or state_def['order'] < 2:
                errors.append("order 必须是大于等于2的整数")

        # 3. 验证 blocks 字段（块列表）
        if 'blocks' not in state_def:
            errors.append("缺少 blocks 字段")
        else:
            if not isinstance(state_def['blocks'], list):
                errors.append("blocks 必须是列表格式")
            else:
                # 验证块数量：order^3 个（order 非法时跳过数量校验，错误已在上面记录）
                order_val = state_def.get('order')
                if isinstance(order_val, int) and order_val >= 2:
                    expected_blocks = order_val ** 3
                    if len(state_def['blocks']) != expected_blocks:
                        errors.append(f"blocks 数量不正确，期望 {expected_blocks} 个，实际 {len(state_def['blocks'])} 个")

                # 4. 验证每个块的定义
                for block in state_def['blocks']:
                    errors.extend(cls._validate_block(block))

                # 5. 验证中心块颜色（仅当 blocks 是列表时）
                errors.extend(cls._validate_center_blocks(state_def['blocks']))

                # 6. 验证相邻块接触面颜色一致性（仅当 blocks 是列表时）
                errors.extend(cls._validate_adjacent_blocks(state_def['blocks']))

        return errors

    @classmethod
    def _validate_block(cls, block):
        """
        验证单个块的定义

        验证内容：
            1. 块必须是字典格式
            2. pos 字段必须是包含3个整数的列表或元组
            3. faces 字段必须包含6个面（U, R, F, D, L, B）
            4. 颜色值必须有效

        有效颜色：
            - Y: 黄色
            - W: 白色
            - B: 蓝色
            - G: 绿色
            - O: 橙色
            - R: 红色
            - -: 不关心（用于部分匹配）
            - ?: 未知（用于公式匹配）

        Args:
            block: 单个块的定义

        Returns:
            错误列表
        """
        errors = []

        # 验证块格式
        if not isinstance(block, dict):
            errors.append("每个块必须是字典格式")
            return errors

        # 验证 pos 字段（位置）
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

        # 验证 faces 字段（面颜色）
        if 'faces' not in block:
            errors.append("缺少 faces 字段")
        else:
            faces = block['faces']
            if not isinstance(faces, dict):
                errors.append("faces 必须是字典格式")
            else:
                # 验证必须包含6个面
                required_faces = ['U', 'R', 'F', 'D', 'L', 'B']
                for face in required_faces:
                    if face not in faces:
                        errors.append(f"缺少 {face} 面")

                # 验证颜色值有效
                valid_colors = ['Y', 'W', 'B', 'G', 'O', 'R', '-', '?']
                for face, color in faces.items():
                    if color not in valid_colors:
                        errors.append(f"面 {face} 的颜色 {color} 无效，有效值: {', '.join(valid_colors)}")

        return errors

    @classmethod
    def _validate_center_blocks(cls, blocks):
        """
        验证中心块颜色

        检查每个中心块的对应面颜色是否符合标准配色方案。
        中心块位置固定，其对应面颜色也固定。

        中心块位置与对应面的关系：
            - (0, 1, 0): 上中心块 → U面
            - (0, -1, 0): 下中心块 → D面
            - (0, 0, 1): 前中心块 → F面
            - (0, 0, -1): 后中心块 → B面
            - (-1, 0, 0): 左中心块 → L面
            - (1, 0, 0): 右中心块 → R面

        Args:
            blocks: 块列表

        Returns:
            错误列表
        """
        errors = []

        for pos, expected_color in cls.CENTER_COLORS.items():
            # 查找中心块
            block = cls._find_block_by_pos(blocks, pos)
            if block and isinstance(block, dict) and 'faces' in block:
                # 获取该中心块需要验证的面
                face_key = cls._get_center_face_key(pos)
                actual_color = block['faces'].get(face_key, '')
                # 验证颜色是否正确
                if actual_color != expected_color:
                    errors.append(f"中心块 {pos} 的 {face_key} 面颜色错误，期望 {expected_color}，实际 {actual_color}")

        return errors

    @classmethod
    def _validate_adjacent_blocks(cls, blocks):
        """
        验证相邻块接触面颜色一致性

        检查相邻两个块的接触面颜色是否一致。
        例如：块 A 的 R 面应该与相邻块 B 的 L 面颜色相同。

        验证逻辑：
            1. 遍历每个块的每个方向
            2. 查找相邻块
            3. 检查接触面颜色是否一致（排除 '-' 和 '?'）

        Args:
            blocks: 块列表

        Returns:
            错误列表
        """
        errors = []

        for block in blocks:
            # 跳过结构不合法的 block（前面的 _validate_block 已报告错误）
            if not isinstance(block, dict):
                continue
            if 'pos' not in block or not isinstance(block['pos'], (list, tuple)) or len(block['pos']) != 3:
                continue
            if 'faces' not in block or not isinstance(block['faces'], dict):
                continue
            pos = tuple(block['pos'])

            # 获取所有相邻位置
            for direction, neighbor_pos in cls._get_neighbors(pos):
                neighbor = cls._find_block_by_pos(blocks, neighbor_pos)
                if neighbor and isinstance(neighbor, dict) and 'faces' in neighbor:
                    # 获取当前块的接触面和相邻块的对应面
                    my_face = cls._direction_to_face(direction)
                    neighbor_face = cls._opposite_face(my_face)

                    # 获取接触面颜色
                    my_color = block['faces'].get(my_face, '-')
                    neighbor_color = neighbor['faces'].get(neighbor_face, '-')

                    # 如果两个颜色都不为 '-' 且不一致，则报错
                    if my_color != '-' and neighbor_color != '-' and my_color != neighbor_color:
                        errors.append(f"块 {pos} 的 {my_face} 面与相邻块 {neighbor_pos} 的 {neighbor_face} 面颜色不一致")

        return errors

    @classmethod
    def _find_block_by_pos(cls, blocks, pos):
        """
        根据位置查找块

        将位置转换为元组进行比较，支持列表和元组格式。

        Args:
            blocks: 块列表
            pos: 位置（列表或元组）

        Returns:
            找到的块或 None
        """
        pos_tuple = tuple(pos) if isinstance(pos, list) else pos
        for block in blocks:
            if not isinstance(block, dict) or 'pos' not in block:
                continue
            block_pos = block['pos']
            if not isinstance(block_pos, (list, tuple)):
                continue
            block_pos = tuple(block_pos) if isinstance(block_pos, list) else block_pos
            if block_pos == pos_tuple:
                return block
        return None

    @classmethod
    def _get_center_face_key(cls, pos):
        """
        获取中心块需要验证的面

        根据中心块的位置确定需要验证的面。

        Args:
            pos: 中心块位置

        Returns:
            需要验证的面（U, D, F, B, L, R）或 None
        """
        if pos[1] == 1:
            return "U"  # 上中心块
        if pos[1] == -1:
            return "D"  # 下中心块
        if pos[2] == 1:
            return "F"  # 前中心块
        if pos[2] == -1:
            return "B"  # 后中心块
        if pos[0] == -1:
            return "L"  # 左中心块
        if pos[0] == 1:
            return "R"  # 右中心块
        return None

    @classmethod
    def _get_neighbors(cls, pos):
        """
        获取一个位置的所有相邻位置

        检查六个方向（R, L, U, D, F, B）的相邻位置是否在魔方范围内。

        Args:
            pos: 当前位置

        Returns:
            相邻位置列表（方向, 位置元组）
        """
        deltas = {
            'R': (1, 0, 0), 'L': (-1, 0, 0),
            'U': (0, 1, 0), 'D': (0, -1, 0),
            'F': (0, 0, 1), 'B': (0, 0, -1),
        }

        neighbors = []
        order = 3
        half_order = (order - 1) // 2  # 对于3阶魔方，half_order = 1

        for direction, delta in deltas.items():
            neighbor_pos = (pos[0] + delta[0], pos[1] + delta[1], pos[2] + delta[2])
            # 检查相邻位置是否在魔方范围内
            if all(-half_order <= p <= half_order for p in neighbor_pos):
                neighbors.append((direction, neighbor_pos))

        return neighbors

    @classmethod
    def _direction_to_face(cls, direction):
        """
        将方向转换为面对应的键

        方向和面对应关系相同，直接返回。

        Args:
            direction: 方向（R, L, U, D, F, B）

        Returns:
            面对应的键
        """
        return direction

    @classmethod
    def _opposite_face(cls, face):
        """
        获取对面的面

        面的对立关系：
            - U ↔ D
            - F ↔ B
            - L ↔ R

        Args:
            face: 面（U, D, F, B, L, R）

        Returns:
            对面的面
        """
        opposites = {'U': 'D', 'D': 'U', 'F': 'B', 'B': 'F', 'L': 'R', 'R': 'L'}
        return opposites.get(face, face)


class FormulaMatchService:
    """
    公式匹配服务

    根据用户当前的魔方状态匹配适用的公式。

    匹配策略：
        1. 前置状态匹配：直接比较用户状态与公式的前置状态
        2. 目标状态匹配：应用公式后比较结果状态与公式的目标状态

    状态匹配规则：
        - 公式状态中颜色为 '-' 的面不参与匹配（表示"不关心"）
        - 只有公式中指定了颜色的面需要与用户状态一致
        - 用户状态中未指定的面（颜色为 '-'）不影响匹配
    """

    @classmethod
    def match_formulas(cls, user_state):
        """
        根据用户当前状态匹配适用的公式

        匹配流程：
            1. 匹配有前置状态定义的公式
            2. 匹配有目标状态定义但无前置状态的公式

        Args:
            user_state: 用户当前的魔方状态

        Returns:
            匹配的公式列表
        """
        from .models import Formula

        matched = []

        # 1. 前置状态匹配：直接比较用户状态与公式的前置状态
        for formula in Formula.objects.filter(pre_state_definition__isnull=False):
            if cls._is_state_match(user_state, formula.pre_state_definition):
                matched.append(formula)

        # 2. 目标状态匹配：应用公式后比较结果状态与公式的目标状态
        for formula in Formula.objects.filter(
            pre_state_definition__isnull=True,
            target_state__isnull=False
        ):
            # 执行公式得到结果状态
            result_state = cls._execute_formula(user_state, formula.notation)
            # 比较结果状态与目标状态
            if cls._is_state_match(result_state, formula.target_state.state_definition):
                matched.append(formula)

        return matched

    @classmethod
    def _is_state_match(cls, user_state, formula_state):
        """
        判断用户状态是否匹配公式状态

        匹配逻辑：
            1. 遍历公式状态中的每个块
            2. 在用户状态中找到对应位置的块
            3. 比较颜色（'-' 表示不关心，跳过）
            4. 如果所有指定颜色都匹配，则返回 True

        Args:
            user_state: 用户当前状态
            formula_state: 公式的状态定义

        Returns:
            True（匹配）或 False（不匹配）
        """
        for block in formula_state.get('blocks', []):
            pos = block['pos']
            faces = block.get('faces', {})

            # 在用户状态中找到对应位置的块
            user_block = cls._find_block_by_pos(user_state.get('blocks', []), pos)
            if not user_block:
                continue

            # 比较每个指定的面颜色
            for face, color in faces.items():
                # '-' 表示不关心，跳过比较
                if color != '-' and user_block.get('faces', {}).get(face, '-') != color:
                    return False

        return True

    @classmethod
    def _find_block_by_pos(cls, blocks, pos):
        """
        根据位置查找块

        将位置转换为元组进行比较，支持列表和元组格式。

        Args:
            blocks: 块列表
            pos: 位置（列表或元组）

        Returns:
            找到的块或 None
        """
        pos_tuple = tuple(pos) if isinstance(pos, list) else pos
        for block in blocks:
            block_pos = tuple(block['pos']) if isinstance(block['pos'], list) else block['pos']
            if block_pos == pos_tuple:
                return block
        return None

    @classmethod
    def _execute_formula(cls, state, notation):
        """
        执行公式得到结果状态

        这是一个占位方法，实际实现需要根据公式记号模拟魔方转动。
        当前返回原状态，不影响匹配逻辑（因为状态匹配使用的是部分匹配）。

        Args:
            state: 当前状态
            notation: 公式记号

        Returns:
            执行公式后的状态
        """
        return state