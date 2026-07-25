from PIL import Image
from io import BytesIO
import os


def compress_image(file, max_width=1200, max_height=1200, quality=85, output_format='JPEG'):
    img = Image.open(file)
    file.seek(0)

    if img.mode in ('RGBA', 'LA'):
        if output_format == 'JPEG':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert('RGBA')

    width, height = img.size
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format=output_format, quality=quality, optimize=True)
    buffer.seek(0)

    return buffer


def convert_to_webp(file, quality=85):
    img = Image.open(file)
    file.seek(0)

    buffer = BytesIO()
    img.save(buffer, format='WEBP', quality=quality, lossless=False)
    buffer.seek(0)

    return buffer


def crop_to_square(file):
    img = Image.open(file)
    file.seek(0)

    width, height = img.size
    size = min(width, height)
    left = (width - size) // 2
    top = (height - size) // 2
    right = left + size
    bottom = top + size

    img = img.crop((left, top, right, bottom))

    buffer = BytesIO()
    if img.mode in ('RGBA', 'LA'):
        img.save(buffer, format='PNG', optimize=True)
    else:
        img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)

    return buffer


def process_image(file, max_width=1200, max_height=1200, quality=85, crop_square=False, convert_webp=False):
    img = Image.open(file)
    file.seek(0)

    if crop_square:
        width, height = img.size
        size = min(width, height)
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        img = img.crop((left, top, right, bottom))

    width, height = img.size
    if width > max_width or height > max_height:
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        img = img.resize((new_width, new_height), Image.LANCZOS)

    buffer = BytesIO()
    output_format = 'WEBP' if convert_webp else 'JPEG'
    img.save(buffer, format=output_format, quality=quality, optimize=True)
    buffer.seek(0)

    return buffer
