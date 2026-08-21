#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 转 PDF 工具

支持单文件、目录批量、递归子目录，输出到 md 文件所在目录。
不传参数时以交互方式确认配置。
"""

import os
import sys
import argparse
import glob
from pathlib import Path
from datetime import datetime

# ==================== 默认配置 ====================
DEFAULT_CONFIG = {
    'page_size': 'A4',
    'enable_mermaid': True,
    'enable_toc': True,
    'overwrite': True,
}
# ==================================================


def check_dependencies():
    """检查 md2pdf-mermaid 是否已安装"""
    try:
        import md2pdf  # noqa: F401
        return True
    except ImportError:
        print("❌ md2pdf-mermaid 未安装")
        print("请运行以下命令安装:")
        print("  pip install md2pdf-mermaid")
        print("  playwright install chromium")
        return False


def check_playwright():
    """检查 Playwright 浏览器是否已安装（懒加载，转换前再调）"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        return True
    except Exception:
        print("❌ Playwright 浏览器未安装或配置错误")
        print("请运行: playwright install chromium")
        return False


def get_md_files(target_path, recursive=False):
    """
    获取指定路径下的所有 .md 文件

    Args:
        target_path: 文件或目录路径
        recursive: 是否递归子目录

    Returns:
        list: 排序后的 md 文件绝对路径列表
    """
    target = Path(target_path).resolve()

    # 单个文件
    if target.is_file():
        if target.suffix.lower() == '.md':
            return [str(target)]
        return []

    # 目录
    if recursive:
        pattern = os.path.join(str(target), '**', '*.md')
        md_files = glob.glob(pattern, recursive=True)
    else:
        pattern = os.path.join(str(target), '*.md')
        md_files = glob.glob(pattern)

    # 过滤排除目录
    exclude_patterns = ['node_modules', '.git', 'venv', '__pycache__', '.dev-local']
    md_files = [f for f in md_files if not any(p in f.replace('\\', '/') for p in exclude_patterns)]

    return sorted(md_files)


def get_output_path(md_file, overwrite=True):
    """生成 PDF 输出路径（与 md 文件同目录）"""
    md_path = Path(md_file)
    base_name = md_path.stem
    pdf_path = md_path.parent / f"{base_name}.pdf"

    if not overwrite and pdf_path.exists():
        counter = 1
        while True:
            new_path = pdf_path.parent / f"{base_name}_{counter}.pdf"
            if not new_path.exists():
                pdf_path = new_path
                break
            counter += 1

    return pdf_path


def convert_md_to_pdf(md_file, pdf_path, config):
    """转换单个 Markdown 文件为 PDF"""
    try:
        from md2pdf import convert_markdown_to_pdf_html

        print(f"   📄 转换中: {os.path.basename(md_file)}")

        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        if not md_content.strip():
            print(f"      ⚠️  文件为空，跳过")
            return False

        convert_kwargs = {
            'title': os.path.basename(md_file).replace('.md', ''),
            'page_size': config['page_size'],
            'enable_mermaid': config['enable_mermaid'],
            'enable_toc': config['enable_toc'],
        }

        convert_markdown_to_pdf_html(md_content, str(pdf_path), **convert_kwargs)

        file_size = os.path.getsize(pdf_path) / 1024
        print(f"      ✅ 生成成功: {pdf_path.name} ({file_size:.2f} KB)")
        return True

    except TypeError as e:
        if "unexpected keyword argument" in str(e):
            print(f"      ⚠️  参数不兼容，尝试使用默认配置...")
            try:
                from md2pdf import convert_markdown_to_pdf_html
                convert_markdown_to_pdf_html(md_content, str(pdf_path))
                file_size = os.path.getsize(pdf_path) / 1024
                print(f"      ✅ 生成成功: {pdf_path.name} ({file_size:.2f} KB)")
                return True
            except Exception as e2:
                print(f"      ❌ 转换失败: {e2}")
                return False
        else:
            print(f"      ❌ 转换失败: {e}")
            return False
    except Exception as e:
        print(f"      ❌ 转换失败: {e}")
        return False


def interactive_prompt_path():
    """交互询问目标路径"""
    default_path = '.'
    user_input = input(f"请输入 md 文件或目录路径（回车={default_path}）: ").strip()
    if not user_input:
        user_input = default_path
    return user_input


def interactive_prompt_recursive():
    """交互询问是否递归子目录"""
    user_input = input("是否递归子目录？(y/N): ").strip().lower()
    return user_input == 'y'


def interactive_confirm(md_files, config, target_path, recursive):
    """展示扫描结果和配置，交互确认是否继续"""
    print(f"\n📁 目标路径: {Path(target_path).resolve()}")
    print(f"🔄 递归模式: {'是' if recursive else '否'}")
    print(f"📋 找到 {len(md_files)} 个 Markdown 文件:")
    for i, f in enumerate(md_files, 1):
        print(f"   {i}. {os.path.basename(f)}")

    print("\n⚙️  转换配置:")
    print(f"   - 页面大小: {config['page_size']}")
    print(f"   - 启用 Mermaid: {config['enable_mermaid']}")
    print(f"   - 生成目录: {config['enable_toc']}")
    print(f"   - 覆盖已存在: {'是' if config['overwrite'] else '否'}")
    print(f"   - 输出位置: 与源文件同目录")

    response = input(f"\n是否继续转换 {len(md_files)} 个文件？(y/N): ").strip().lower()
    return response == 'y'


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='Markdown 转 PDF 工具（支持单文件/目录/递归，输出到源文件同目录）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python md2pdf_converter.py                      # 交互模式
  python md2pdf_converter.py docs/                # 转 docs 目录（不递归）
  python md2pdf_converter.py docs/ -r             # 转 docs 目录（递归子目录）
  python md2pdf_converter.py readme.md            # 转单个文件
  python md2pdf_converter.py docs/ -r -y          # 递归转换，跳过所有确认
        """,
    )
    parser.add_argument(
        'path',
        nargs='?',
        default=None,
        help='md 文件或目录路径（不传则交互询问，默认当前目录）',
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        default=False,
        help='递归子目录（默认不递归）',
    )
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        default=False,
        help='跳过所有确认，直接执行（默认交互确认）',
    )
    parser.add_argument(
        '--page-size',
        default='A4',
        help='页面大小，默认 A4',
    )
    parser.add_argument(
        '--no-toc',
        action='store_true',
        default=False,
        help='不生成目录',
    )
    parser.add_argument(
        '--no-mermaid',
        action='store_true',
        default=False,
        help='禁用 Mermaid 图表渲染',
    )
    parser.add_argument(
        '--no-overwrite',
        action='store_true',
        default=False,
        help='不覆盖已存在的 PDF（自动重命名）',
    )
    return parser.parse_args()


def build_config(args):
    """根据参数构建配置"""
    return {
        'page_size': args.page_size,
        'enable_mermaid': not args.no_mermaid,
        'enable_toc': not args.no_toc,
        'overwrite': not args.no_overwrite,
    }


def main():
    args = parse_args()
    config = build_config(args)

    print("=" * 70)
    print("📚 Markdown 转 PDF 工具")
    print("=" * 70)

    # 1. 确定目标路径
    target_path = args.path
    interactive = not args.yes

    if target_path is None and interactive:
        target_path = interactive_prompt_path()
    elif target_path is None:
        target_path = '.'

    target_path = os.path.expanduser(target_path)

    if not Path(target_path).exists():
        print(f"❌ 路径不存在: {target_path}")
        return 1

    # 2. 确定是否递归
    recursive = args.recursive
    if not recursive and interactive and Path(target_path).is_dir():
        recursive = interactive_prompt_recursive()

    # 3. 依赖检查（md2pdf 模块）
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请先安装所需依赖")
        return 1

    # 4. 扫描 md 文件
    print(f"\n🔍 正在扫描 Markdown 文件...")
    md_files = get_md_files(target_path, recursive=recursive)

    if not md_files:
        print("⚠️  未找到 Markdown 文件")
        return 0

    # 5. 单文件模式直接转换，批量模式先确认
    is_single = Path(target_path).is_file()

    if is_single:
        print(f"📝 单文件模式: {os.path.basename(md_files[0])}")
        if interactive:
            response = input("是否转换？(y/N): ").strip().lower()
            if response != 'y':
                print("❌ 已取消")
                return 0
    else:
        if interactive and not interactive_confirm(md_files, config, target_path, recursive):
            print("❌ 已取消")
            return 0

    # 6. Playwright 检查（懒加载，真正转换前才检查）
    print("\n🔍 检查 Playwright 浏览器...")
    if not check_playwright():
        return 1

    # 7. 开始转换
    print("\n🔄 开始转换...")
    print("-" * 70)

    success_count = 0
    fail_count = 0
    failed_files = []
    start_time = datetime.now()

    for i, md_file in enumerate(md_files, 1):
        pdf_path = get_output_path(md_file, overwrite=config['overwrite'])
        print(f"\n[{i}/{len(md_files)}] 📝 {os.path.basename(md_file)}")
        print(f"   📁 输出: {pdf_path}")

        if convert_md_to_pdf(md_file, pdf_path, config):
            success_count += 1
        else:
            fail_count += 1
            failed_files.append(md_file)

    elapsed_time = datetime.now() - start_time

    # 8. 结果汇总
    print("\n" + "=" * 70)
    print("📊 转换完成!")
    print(f"   ✅ 成功: {success_count} 个文件")
    if fail_count > 0:
        print(f"   ❌ 失败: {fail_count} 个文件")
        print("\n失败的文件:")
        for f in failed_files:
            print(f"   - {f}")
    print(f"   ⏱️  总耗时: {elapsed_time.total_seconds():.2f} 秒")
    print("=" * 70)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit(main())
