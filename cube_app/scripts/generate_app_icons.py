"""
从 cube.svg 生成 Android 应用图标各尺寸 PNG
"""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
SVG_PATH = BASE_DIR.parent / "cube_front" / "src" / "assets" / "cube.svg"
RES_DIR = BASE_DIR / "android" / "app" / "src" / "main" / "res"

SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

svg_content = SVG_PATH.read_text(encoding="utf-8")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()

    for folder, size in SIZES.items():
        folder_path = RES_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        icon_size = int(size * 0.72)

        # 方形图标（白色背景）
        html = f"""
        <div style="width:{size}px;height:{size}px;background:#ffffff;display:flex;align-items:center;justify-content:center;">
            {svg_content.replace('width="200"', f'width="{icon_size}"').replace('height="200"', f'height="{icon_size}"')}
        </div>"""
        page.set_content(html)
        div = page.query_selector("div")
        div.screenshot(path=str(folder_path / "ic_launcher.png"), type="png")

        # 圆形图标
        html_round = f"""
        <div style="width:{size}px;height:{size}px;background:#ffffff;border-radius:50%;display:flex;align-items:center;justify-content:center;overflow:hidden;">
            {svg_content.replace('width="200"', f'width="{int(size * 0.62)}"').replace('height="200"', f'height="{int(size * 0.62)}"')}
        </div>"""
        page.set_content(html_round)
        div = page.query_selector("div")
        div.screenshot(path=str(folder_path / "ic_launcher_round.png"), type="png")

        # 前景图（adaptive icon，透明背景）
        html_fg = f"""
        <div style="width:{size}px;height:{size}px;display:flex;align-items:center;justify-content:center;">
            {svg_content.replace('width="200"', f'width="{int(size * 0.75)}"').replace('height="200"', f'height="{int(size * 0.75)}"')}
        </div>"""
        page.set_content(html_fg)
        div = page.query_selector("div")
        div.screenshot(path=str(folder_path / "ic_launcher_foreground.png"), type="png", omit_background=True)

        print(f"✓ {folder} ({size}px)")

    browser.close()

print("\n全部图标生成完成")
