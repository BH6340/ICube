#!/usr/bin/env python3
"""Commit message 规范检查，匹配 .trae/rules/git-commit-message.md 规则"""
import re
import sys

VALID_TYPES = {
    'feat', 'fix', 'docs', 'style', 'refactor',
    'perf', 'test', 'chore', 'build', 'ci',
}
MAX_SUBJECT_LEN = 50
MAX_HEADER_LEN = 100
MAX_BODY_LINE_LEN = 72

PATTERN = re.compile(r'^(\w+)(\(.+\))?: (.+)$')


def check(message: str) -> list[str]:
    errors = []
    lines = message.strip().split('\n')
    header = lines[0] if lines else ''

    match = PATTERN.match(header)
    if not match:
        errors.append(f'header 格式错误，应为 type(scope?): subject，实际: {header}')
        return errors

    commit_type = match.group(1)
    subject = match.group(3)

    if commit_type not in VALID_TYPES:
        errors.append(f'type 必须为 {", ".join(sorted(VALID_TYPES))} 之一，实际: {commit_type}')

    if len(subject) > MAX_SUBJECT_LEN:
        errors.append(f'subject 长度 {len(subject)} 超过 {MAX_SUBJECT_LEN} 字')

    if subject.endswith('.') or subject.endswith('。'):
        errors.append('subject 结尾不能加句号')

    if len(header) > MAX_HEADER_LEN:
        errors.append(f'header 长度 {len(header)} 超过 {MAX_HEADER_LEN} 字')

    if len(lines) > 1:
        if lines[1].strip():
            errors.append('subject 与 body 之间必须空一行')
        for i, line in enumerate(lines[2:], start=3):
            if line.strip() and len(line) > MAX_BODY_LINE_LEN:
                errors.append(f'body 第 {i - 2} 行长度 {len(line)} 超过 {MAX_BODY_LINE_LEN} 字')

    return errors


def _p(s: str) -> None:
    """安全打印，避免 Windows GBK 控制台编码错误"""
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))


def main() -> None:
    # 强制 stdout 使用 UTF-8，避免 Windows GBK 控制台编码错误
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    if len(sys.argv) < 2:
        _p('用法: check_commit_msg.py <commit_msg_file>')
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        raw = f.read()

    message = '\n'.join(line for line in raw.split('\n') if not line.startswith('#'))

    errors = check(message)
    if errors:
        _p('[x] Commit message 检查未通过:\n')
        for e in errors:
            _p(f'  - {e}')
        _p(f'\n当前: {message.split(chr(10))[0]}')
        _p('\n格式: type(scope?): subject')
        _p(f'type: {", ".join(sorted(VALID_TYPES))}')
        _p(f'subject: 中文，≤{MAX_SUBJECT_LEN}字，不加句号')
        _p('示例: feat(forum): 帖子列表支持按热度排序')
        sys.exit(1)

    _p('[v] Commit message 检查通过')
    sys.exit(0)


if __name__ == '__main__':
    main()
