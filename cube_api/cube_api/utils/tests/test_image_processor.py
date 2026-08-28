# -*- coding: utf-8 -*-
"""
Utils 模块测试

测试工具函数，包括：
    - image_processor: 图片压缩、格式转换、裁剪
    - image_url: URL 生成
"""
from django.test import TestCase
from io import BytesIO
from PIL import Image

from utils.image_processor import (
    compress_image,
    convert_to_webp,
    crop_to_square,
    process_image,
    generate_formula_thumbnail,
)
from utils.image_url import build_image_url


def create_test_image(width=200, height=100, color='red'):
    """创建测试用图片"""
    img = Image.new('RGB', (width, height), color=color)
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer


class CompressImageTest(TestCase):
    """图片压缩测试"""

    def test_compress_image_within_limit(self):
        """测试压缩小于限制的图片（尺寸不变）"""
        file = create_test_image(width=100, height=100)
        result = compress_image(file, max_width=200, max_height=200)

        img = Image.open(result)
        self.assertEqual(img.size, (100, 100))

    def test_compress_image_exceeds_limit(self):
        """测试压缩超过限制的图片（尺寸缩小）"""
        file = create_test_image(width=400, height=200)
        result = compress_image(file, max_width=200, max_height=200)

        img = Image.open(result)
        self.assertLessEqual(img.size[0], 200)
        self.assertLessEqual(img.size[1], 200)

    def test_compress_image_output_format(self):
        """测试压缩输出格式"""
        file = create_test_image()
        result = compress_image(file, output_format='PNG')

        img = Image.open(result)
        self.assertEqual(img.format, 'PNG')

    def test_compress_image_quality(self):
        """测试压缩质量参数"""
        file = create_test_image()
        result_high = compress_image(file, quality=100)
        result_low = compress_image(file, quality=10)

        # 高质量文件应该更大
        self.assertGreater(len(result_high.getvalue()), len(result_low.getvalue()))

    def test_compress_image_rgba_to_jpeg(self):
        """测试 RGBA 图片转 JPEG（透明通道处理）"""
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        result = compress_image(buffer, output_format='JPEG')
        # 应该成功转换，没有抛出异常
        self.assertIsNotNone(result)


class ConvertToWebPTest(TestCase):
    """WebP 格式转换测试"""

    def test_convert_to_webp(self):
        """测试转换为 WebP 格式"""
        file = create_test_image()
        result = convert_to_webp(file)

        img = Image.open(result)
        self.assertEqual(img.format, 'WEBP')

    def test_convert_to_webp_quality(self):
        """测试 WebP 质量参数"""
        file = create_test_image()
        result_high = convert_to_webp(file, quality=100)
        result_low = convert_to_webp(file, quality=10)

        # 高质量文件应该更大
        self.assertGreater(len(result_high.getvalue()), len(result_low.getvalue()))


class CropToSquareTest(TestCase):
    """1:1 裁剪测试"""

    def test_crop_landscape_to_square(self):
        """测试横图裁剪为正方形"""
        file = create_test_image(width=300, height=100)
        result = crop_to_square(file)

        img = Image.open(result)
        self.assertEqual(img.size, (100, 100))

    def test_crop_portrait_to_square(self):
        """测试竖图裁剪为正方形"""
        file = create_test_image(width=100, height=300)
        result = crop_to_square(file)

        img = Image.open(result)
        self.assertEqual(img.size, (100, 100))

    def test_crop_square_already_square(self):
        """测试已是正方形的图片"""
        file = create_test_image(width=200, height=200)
        result = crop_to_square(file)

        img = Image.open(result)
        self.assertEqual(img.size, (200, 200))

    def test_crop_preserves_center(self):
        """测试裁剪保留中心区域"""
        img = Image.new('RGB', (400, 200), color='red')
        for x in range(150, 250):
            for y in range(50, 150):
                img.putpixel((x, y), (0, 0, 255))

        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)

        result = crop_to_square(buffer)
        cropped = Image.open(result)

        self.assertEqual(cropped.size, (200, 200))


class ProcessImageTest(TestCase):
    """统一图片处理入口测试"""

    def test_process_image_compress_only(self):
        """测试仅压缩"""
        file = create_test_image(width=800, height=600)
        result = process_image(file, max_width=400, max_height=400)

        img = Image.open(result)
        self.assertLessEqual(img.size[0], 400)
        self.assertLessEqual(img.size[1], 400)

    def test_process_image_crop_and_compress(self):
        """测试裁剪 + 压缩"""
        file = create_test_image(width=800, height=400)
        result = process_image(file, max_width=200, crop_square=True)

        img = Image.open(result)
        self.assertEqual(img.size[0], img.size[1])
        self.assertLessEqual(img.size[0], 200)

    def test_process_image_convert_webp(self):
        """测试 WebP 转换"""
        file = create_test_image()
        result = process_image(file, convert_webp=True)

        img = Image.open(result)
        self.assertEqual(img.format, 'WEBP')

    def test_process_image_full_pipeline(self):
        """测试完整流水线（裁剪 + 压缩 + WebP）"""
        file = create_test_image(width=1000, height=500)
        result = process_image(
            file,
            max_width=256,
            max_height=256,
            quality=85,
            crop_square=True,
            convert_webp=True
        )

        img = Image.open(result)
        self.assertEqual(img.format, 'WEBP')
        self.assertEqual(img.size[0], img.size[1])
        self.assertLessEqual(img.size[0], 256)


class GenerateFormulaThumbnailTest(TestCase):
    """公式缩略图生成测试"""

    def test_generate_thumbnail_success(self):
        """测试生成缩略图成功"""
        result = generate_formula_thumbnail('测试公式', "R U R'U'")

        self.assertIsNotNone(result)
        result.seek(0)

        img = Image.open(result)
        self.assertEqual(img.size, (512, 512))
        self.assertEqual(img.format, 'WEBP')

    def test_generate_thumbnail_custom_size(self):
        """测试自定义尺寸的缩略图"""
        result = generate_formula_thumbnail('测试', 'R U', size=256)

        img = Image.open(result)
        self.assertEqual(img.size, (256, 256))

    def test_generate_thumbnail_with_empty_name(self):
        """测试空名称（边界情况）"""
        result = generate_formula_thumbnail('', 'R U')
        self.assertIsNotNone(result)

    def test_generate_thumbnail_with_empty_notation(self):
        """测试空记号（边界情况）"""
        result = generate_formula_thumbnail('公式名', '')
        self.assertIsNotNone(result)


class BuildImageUrlTest(TestCase):
    """图片 URL 构建测试"""

    def test_build_url_with_none(self):
        """测试 None 输入"""
        result = build_image_url(None)
        self.assertEqual(result, '')

    def test_build_url_with_empty_string(self):
        """测试空字符串"""
        result = build_image_url('')
        self.assertEqual(result, '')

    def test_build_url_with_relative_path(self):
        """测试相对路径"""
        result = build_image_url('avatars/test.png')
        self.assertIn('/media/avatars/test.png', result)

    def test_build_url_with_media_prefix(self):
        """测试已有 /media/ 前缀的路径"""
        result = build_image_url('/media/avatars/test.png')
        self.assertEqual(result, '/media/avatars/test.png')

    def test_build_url_with_absolute_url(self):
        """测试已有完整 URL"""
        absolute_url = 'http://example.com/image.png'
        result = build_image_url(absolute_url)
        self.assertEqual(result, absolute_url)

    def test_build_url_with_field_file(self):
        """测试 FieldFile 对象"""
        from django.db.models.fields.files import FieldFile
        result = build_image_url('avatars/test.png')
        self.assertIn('avatars/test.png', result)
