# -*- coding: utf-8 -*-
"""
图片处理工具模块

该模块提供了图片处理的完整流水线，包括压缩、裁剪、格式转换和缩略图生成功能。

主要函数：
    - compress_image: 图片压缩（尺寸缩放 + 质量优化）
    - convert_to_webp: 格式转换为 WebP
    - crop_to_square: 1:1 比例裁剪
    - process_image: 统一处理入口（压缩 + 裁剪 + 格式转换）
    - generate_formula_thumbnail: 自动生成公式缩略图

设计特点：
    - 使用 Pillow 库进行图片处理
    - 大图预压缩：原图>2048px 时先缩小再裁剪
    - 1:1 裁剪：中心裁剪为正方形
    - WebP 转换：减小文件体积 50%+
    - 支持 RGBA/LA 等透明通道图片的转换
"""
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os


def compress_image(file, max_width=1200, max_height=1200, quality=85, output_format='JPEG'):
    """
    图片压缩

    对上传的图片进行尺寸缩放和质量优化，支持透明通道处理。

    Args:
        file: 上传的图片文件（支持 file-like 对象）
        max_width: 最大宽度（像素），默认 1200
        max_height: 最大高度（像素），默认 1200
        quality: JPEG/WebP 质量（1-100），默认 85
        output_format: 输出格式（JPEG/PNG/WEBP），默认 JPEG

    Returns:
        BytesIO: 压缩后的图片二进制流

    设计说明：
        - 透明通道图片（RGBA/LA）转为 JPEG 时会填充白色背景
        - 超过最大尺寸的图片会等比例缩放
        - 使用 LANCZOS 算法进行高质量缩放
    """
    # 使用 Pillow 打开图片
    img = Image.open(file)
    # 重置文件指针，以便后续可能的读取
    file.seek(0)

    # 处理透明通道：转为 JPEG 时需要填充背景
    if img.mode in ('RGBA', 'LA'):
        if output_format == 'JPEG':
            # 创建白色背景并粘贴原图片
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            # 其他格式保留透明通道
            img = img.convert('RGBA')

    # 尺寸缩放：等比例缩放到最大尺寸内
    width, height = img.size
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        # 使用 LANCZOS 算法进行高质量缩放
        img = img.resize((new_width, new_height), Image.LANCZOS)

    # 保存到内存缓冲区
    buffer = BytesIO()
    img.save(buffer, format=output_format, quality=quality, optimize=True)
    buffer.seek(0)

    return buffer


def convert_to_webp(file, quality=85):
    """
    将图片格式转换为 WebP

    WebP 格式相比 JPEG/PNG 能减小 50%+ 的文件体积，适合网络传输。

    Args:
        file: 上传的图片文件
        quality: WebP 质量（0-100），默认 85

    Returns:
        BytesIO: WebP 格式的图片二进制流
    """
    img = Image.open(file)
    file.seek(0)

    buffer = BytesIO()
    # lossless=False 启用有损压缩，体积更小
    img.save(buffer, format='WEBP', quality=quality, lossless=False)
    buffer.seek(0)

    return buffer


def crop_to_square(file):
    """
    将图片裁剪为 1:1 正方形

    采用中心裁剪策略，保留图片中心区域。

    Args:
        file: 上传的图片文件

    Returns:
        BytesIO: 裁剪后的图片二进制流（PNG 或 JPEG 格式）

    设计说明：
        - 裁剪尺寸取原图宽高的较小值
        - 裁剪后根据是否有透明通道选择 PNG 或 JPEG 格式
    """
    img = Image.open(file)
    file.seek(0)

    # 计算中心裁剪区域
    width, height = img.size
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size

    # 执行裁剪
    img = img.crop((left, top, right, bottom))

    buffer = BytesIO()
    # 根据是否有透明通道选择输出格式
    if img.mode in ('RGBA', 'LA'):
        img.save(buffer, format='PNG', optimize=True)
    else:
        img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)

    return buffer


def process_image(file, max_width=1200, max_height=1200, quality=85, crop_square=False, convert_webp=False):
    """
    统一图片处理入口

    整合压缩、裁剪和格式转换功能，支持按需组合。

    Args:
        file: 上传的图片文件
        max_width: 最大宽度（像素），默认 1200
        max_height: 最大高度（像素），默认 1200
        quality: 输出质量（1-100），默认 85
        crop_square: 是否裁剪为 1:1 正方形，默认 False
        convert_webp: 是否转换为 WebP 格式，默认 False

    Returns:
        BytesIO: 处理后的图片二进制流

    使用示例：
        # 仅压缩
        processed = process_image(file, max_width=800)

        # 压缩 + 裁剪 + WebP 转换（公式上传场景）
        processed = process_image(
            file,
            max_width=512,
            max_height=512,
            crop_square=True,
            convert_webp=True
        )

    处理流程：
        1. 可选：中心裁剪为 1:1 正方形
        2. 可选：等比例缩放到最大尺寸内
        3. 可选：转换为 WebP 格式
        4. 保存到内存缓冲区
    """
    img = Image.open(file)
    file.seek(0)

    # 步骤 1：可选的 1:1 裁剪
    if crop_square:
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        img = img.crop((left, top, right, bottom))

    # 步骤 2：可选的尺寸缩放
    width, height = img.size
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)

    # 步骤 3：保存到缓冲区，可选 WebP 格式
    buffer = BytesIO()
    output_format = 'WEBP' if convert_webp else 'JPEG'
    img.save(buffer, format=output_format, quality=quality, optimize=True)
    buffer.seek(0)

    return buffer


def generate_formula_thumbnail(formula_name, formula_notation, size=512):
    """
    自动生成公式缩略图

    根据公式名称和记号生成包含文字的缩略图，用于无上传图片时的默认展示。

    Args:
        formula_name: 公式名称（如 "OLL-01"）
        formula_notation: 公式记号（如 "R U R' U'"）
        size: 缩略图尺寸（像素），默认 512

    Returns:
        BytesIO: WebP 格式的缩略图二进制流

    设计说明：
        - 使用白色背景，灰色文字
        - 公式名称显示在上部，支持自动换行
        - 公式记号显示在下部，支持自动换行
        - 优先使用系统字体（arial.ttf / cour.ttf）
        - 字体加载失败时回退到默认字体
    """
    # 创建白色背景画布
    img = Image.new('RGB', (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 尝试加载系统字体
    try:
        # 名称使用 Arial 字体
        font_name = ImageFont.truetype('arial.ttf', size=24)
        # 记号使用 Courier 等宽字体
        font_notation = ImageFont.truetype('cour.ttf', size=18)
    except IOError:
        # 字体文件不存在时使用默认字体
        font_name = ImageFont.load_default()
        font_notation = ImageFont.load_default()

    # 自动换行处理公式名称
    name_lines = []
    current_line = ''
    for word in formula_name.split():
        test_line = f'{current_line} {word}'.strip()
        # 检查当前行宽度是否超过限制
        if draw.textlength(test_line, font=font_name) < size - 40:
            current_line = test_line
        else:
            name_lines.append(current_line)
            current_line = word
    if current_line:
        name_lines.append(current_line)

    # 自动换行处理公式记号
    notation_lines = []
    current_line = ''
    for step in formula_notation.split():
        test_line = f'{current_line} {step}'.strip()
        if draw.textlength(test_line, font=font_notation) < size - 40:
            current_line = test_line
        else:
            notation_lines.append(current_line)
            current_line = step
    if current_line:
        notation_lines.append(current_line)

    # 绘制公式名称（深灰色，居中显示，最多3行）
    y = 40
    for line in name_lines[:3]:
        text_width = draw.textlength(line, font=font_name)
        x = (size - text_width) // 2
        draw.text((x, y), line, fill=(30, 30, 30), font=font_name)
        y += 35

    # 绘制公式记号（中灰色，居中显示，最多4行）
    y = size - 40 - len(notation_lines) * 25
    for line in notation_lines[:4]:
        text_width = draw.textlength(line, font=font_notation)
        x = (size - text_width) // 2
        draw.text((x, y), line, fill=(80, 80, 80), font=font_notation)
        y += 25

    # 保存为 WebP 格式
    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=85, optimize=True)
    buffer.seek(0)

    return buffer
