import os
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.formula.models import Formula, CubeCategory, FormulaTag, FormulaTagRelation
from apps.formula.services import FormulaService
from utils.image_processor import process_image


class Command(BaseCommand):
    help = '从 JSON 文件导入公式数据（含缩略图压缩）'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='公式 JSON 文件路径'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='已存在同名称公式时，删除后重新导入'
        )

    def handle(self, *args, **options):
        json_file = Path(options['json_file'])

        if not json_file.exists():
            self.stdout.write(self.style.ERROR(f'找不到文件: {json_file}'))
            return

        data_dir = json_file.parent

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        formulas = data.get('formulas', [])
        if not formulas:
            self.stdout.write(self.style.WARNING('JSON 中没有公式数据'))
            return

        self.stdout.write(self.style.SUCCESS(f'开始导入 {len(formulas)} 个公式...'))

        created_count = 0
        skipped_count = 0
        warned_count = 0
        replaced_count = 0
        force = options.get('force', False)

        for formula_data in formulas:
            name = formula_data.get('name', '').strip()
            notation = formula_data.get('notation', '').strip()

            if not name or not notation:
                self.stdout.write(self.style.WARNING('  跳过：名称或公式为空'))
                skipped_count += 1
                continue

            # 匹配分类
            category_name = formula_data.get('category_name', '')
            category = None
            if category_name:
                category = CubeCategory.objects.filter(name=category_name).first()
                if not category:
                    self.stdout.write(self.style.WARNING(
                        f'  分类不存在: {category_name}，跳过此公式'
                    ))
                    warned_count += 1
                    continue

            # 查重
            existing = Formula.objects.filter(name=name, category=category).first()
            if existing and not force:
                self.stdout.write(f'  跳过已存在: {name}')
                skipped_count += 1
                continue

            if existing and force:
                existing.delete()
                self.stdout.write(f'  删除旧公式: {name}')
                replaced_count += 1

            # 处理缩略图
            thumbnail_file = self._process_thumbnail(
                formula_data.get('thumbnail', ''),
                data_dir,
            )

            # 生成逆公式
            inverse_notation = FormulaService.generate_inverse_notation(notation)

            # 创建公式
            formula = Formula.objects.create(
                name=name,
                notation=notation,
                inverse_notation=inverse_notation,
                category=category,
                difficulty=formula_data.get('difficulty', 1),
                description=formula_data.get('description', ''),
                thumbnail=thumbnail_file,
                is_custom=False,
            )

            # 关联标签
            tags = formula_data.get('tags', [])
            for tag_name in tags:
                tag, _ = FormulaTag.objects.get_or_create(name=tag_name)
                FormulaTagRelation.objects.get_or_create(formula=formula, tag=tag)

            created_count += 1
            self.stdout.write(f'  创建公式: {name}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('导入完成！'))
        self.stdout.write(f'  新增: {created_count} 个')
        if replaced_count:
            self.stdout.write(f'  替换: {replaced_count} 个')
        self.stdout.write(f'  跳过: {skipped_count} 个')
        self.stdout.write(f'  警告: {warned_count} 个')

    def _process_thumbnail(self, thumbnail, data_dir):
        if not thumbnail:
            return None

        thumb_path = data_dir / thumbnail
        if not thumb_path.exists():
            self.stdout.write(self.style.WARNING(f'  缩略图不存在: {thumb_path}'))
            return None

        with open(thumb_path, 'rb') as f:
            processed = process_image(
                f,
                max_width=512,
                max_height=512,
                quality=85,
                crop_square=True,
                convert_webp=True,
            )

        base_name = os.path.splitext(os.path.basename(thumbnail))[0]
        new_name = f'{base_name}_thumbnail.webp'

        return InMemoryUploadedFile(
            file=processed,
            field_name='thumbnail',
            name=new_name,
            content_type='image/webp',
            size=processed.getbuffer().nbytes,
            charset=None,
        )
