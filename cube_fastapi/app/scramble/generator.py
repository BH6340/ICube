"""
WCA 标准打乱公式生成器

算法规则：
- 不能连续两步是同一个基础面
- 不能出现 A-对-A 模式（等价于连续转同一面两次对面）
- 二阶只用 U/R/F 三个面
- 三/四/五阶用 U/D/R/L/F/B 六个面
- 四阶及以上增加宽转（Uw/Dw/Rw/Lw/Fw/Bw）

步数遵循 WCA 比赛标准：
- 2x2: 11 步
- 3x3: 20 步
- 4x4: 40 步
- 5x5: 60 步
"""
import random
from typing import List


# 各阶魔方的面列表
_FACES = {
    "2x2": ["U", "R", "F"],
    "3x3": ["U", "D", "R", "L", "F", "B"],
    "4x4": ["U", "D", "R", "L", "F", "B", "Uw", "Dw", "Rw", "Lw", "Fw", "Bw"],
    "5x5": ["U", "D", "R", "L", "F", "B", "Uw", "Dw", "Rw", "Lw", "Fw", "Bw"],
}

# 各阶默认步数（WCA 比赛标准）
_DEFAULT_LENGTH = {
    "2x2": 11,
    "3x3": 20,
    "4x4": 40,
    "5x5": 60,
}

# 转动后缀（顺时针、逆时针、180度）
_SUFFIXES = ["", "'", "2"]

# 对面映射（基础面）
_OPPOSITE = {
    "U": "D", "D": "U",
    "R": "L", "L": "R",
    "F": "B", "B": "F",
}


def _base_face(face: str) -> str:
    """获取面的基础面字符（Uw -> U, R -> R）"""
    return face[0] if face.endswith("w") else face


def generate_scramble(cube_type: str, length: int = None) -> str:
    """
    生成单个打乱公式

    Args:
        cube_type: 魔方类型 ("2x2", "3x3", "4x4", "5x5")
        length: 步数，不传则使用该阶默认值

    Returns:
        空格分隔的打乱序列字符串，如 "R U R' U' ..."

    Raises:
        ValueError: 不支持的魔方类型
    """
    if cube_type not in _FACES:
        raise ValueError(f"不支持的魔方类型: {cube_type}")

    if length is None:
        length = _DEFAULT_LENGTH[cube_type]

    faces = _FACES[cube_type]
    moves: List[str] = []

    while len(moves) < length:
        face = random.choice(faces)
        base = _base_face(face)

        # 规则1: 不能和上一步是同一个基础面
        if moves:
            last_face = moves[-1].rstrip("'2")
            last_base = _base_face(last_face)
            if base == last_base:
                continue

        # 规则2: 不能出现 A-对-A 模式
        if len(moves) >= 2:
            prev2_face = moves[-2].rstrip("'2")
            prev2_base = _base_face(prev2_face)
            if base == prev2_base:
                mid_face = moves[-1].rstrip("'2")
                mid_base = _base_face(mid_face)
                if mid_base == _OPPOSITE.get(base):
                    continue

        suffix = random.choice(_SUFFIXES)
        moves.append(face + suffix)

    return " ".join(moves)


def generate_scramble_batch(cube_type: str, count: int) -> List[str]:
    """批量生成打乱公式"""
    return [generate_scramble(cube_type) for _ in range(count)]


def validate_scramble(scramble: str, cube_type: str) -> bool:
    """验证打乱公式的面是否合法"""
    if cube_type not in _FACES:
        return False
    valid_faces = set(_FACES[cube_type])
    moves = scramble.strip().split()
    for move in moves:
        face = move.rstrip("'2")
        if face not in valid_faces:
            return False
    return True
