"""
打乱公式生成器测试

验证 WCA 标准打乱规则：
- 各阶步数正确
- 不连续同面
- 不出现 A-对-A 模式
- 二阶只用三个面
"""
import pytest

from app.scramble.generator import (
    generate_scramble,
    generate_scramble_batch,
    validate_scramble,
)


def _base(move: str) -> str:
    """提取 move 的基础面字符"""
    face = move.rstrip("'2")
    return face[0] if face.endswith("w") else face


class TestGenerateScramble:
    def test_3x3_default_length(self):
        """三阶默认生成 20 步"""
        result = generate_scramble("3x3")
        moves = result.split()
        assert len(moves) == 20

    def test_2x2_length(self):
        """二阶生成 11 步"""
        result = generate_scramble("2x2")
        moves = result.split()
        assert len(moves) == 11

    def test_4x4_length(self):
        """四阶生成 40 步"""
        result = generate_scramble("4x4")
        moves = result.split()
        assert len(moves) == 40

    def test_5x5_length(self):
        """五阶生成 60 步"""
        result = generate_scramble("5x5")
        moves = result.split()
        assert len(moves) == 60

    def test_no_consecutive_same_face(self):
        """同一基础面不能连续出现两次"""
        for _ in range(100):
            result = generate_scramble("3x3")
            moves = result.split()
            for i in range(len(moves) - 1):
                assert _base(moves[i]) != _base(moves[i + 1]), \
                    f"连续同面: {moves[i]} {moves[i+1]}"

    def test_no_opposite_followed_by_same(self):
        """A面 → 对面 → A面 模式应避免"""
        opposite_pairs = {"U": "D", "D": "U", "R": "L", "L": "R", "F": "B", "B": "F"}
        for _ in range(100):
            result = generate_scramble("3x3")
            moves = result.split()
            faces = [_base(m) for m in moves]
            for i in range(len(faces) - 2):
                if faces[i] == faces[i + 2]:
                    assert faces[i + 1] != opposite_pairs[faces[i]], \
                        f"无效模式: {moves[i]} {moves[i+1]} {moves[i+2]}"

    def test_2x2_only_three_faces(self):
        """二阶只使用 U R F 三个基础面（WCA 标准）"""
        result = generate_scramble("2x2")
        moves = result.split()
        for move in moves:
            assert _base(move) in ("U", "R", "F"), f"二阶出现非法面: {move}"

    def test_invalid_cube_type_raises(self):
        """非法魔方类型抛出 ValueError"""
        with pytest.raises(ValueError):
            generate_scramble("6x6")

    def test_batch_generate(self):
        """批量生成指定数量"""
        results = generate_scramble_batch("3x3", 10)
        assert len(results) == 10
        for r in results:
            assert len(r.split()) == 20

    def test_validate_scramble_valid(self):
        """合法打乱验证通过"""
        s = generate_scramble("3x3")
        assert validate_scramble(s, "3x3") is True

    def test_validate_scramble_invalid(self):
        """非法面验证失败"""
        assert validate_scramble("X Y Z", "3x3") is False
