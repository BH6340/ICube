import os
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.forum.models import Post, PostImage, Tag
from utils.image_processor import process_image

User = get_user_model()

DEFAULT_AUTHOR_EMAIL = 'baihao6340@163.com'


class Command(BaseCommand):
    help = '从 JSON 数据包导入文章（含图片压缩）到论坛'

    def add_arguments(self, parser):
        parser.add_argument(
            'data_dir',
            type=str,
            help='数据包目录路径（包含 articles.json 和 images/）'
        )
        parser.add_argument(
            '--author-id',
            type=int,
            help=f'指定作者 ID（默认使用 {DEFAULT_AUTHOR_EMAIL}）'
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        json_path = data_dir / 'articles.json'

        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f'找不到 articles.json: {json_path}'))
            return

        author = self._resolve_author(options.get('author_id'))
        if not author:
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        articles = data.get('articles', [])
        if not articles:
            self.stdout.write(self.style.WARNING('articles.json 中没有文章数据'))
            return

        self.stdout.write(self.style.SUCCESS(f'开始导入 {len(articles)} 篇文章...'))

        created_count = 0
        skipped_count = 0

        for article_data in articles:
            title = article_data.get('title', '').strip()
            if not title:
                self.stdout.write(self.style.WARNING('  跳过：标题为空'))
                skipped_count += 1
                continue

            if Post.objects.filter(title=title).exists():
                self.stdout.write(f'  跳过已存在: {title[:40]}')
                skipped_count += 1
                continue

            content_md = article_data.get('content_md', '')
            content = article_data.get('content', '') or content_md

            post = Post.objects.create(
                title=title,
                content=content,
                content_md=content_md,
                author=author,
                status='published',
            )

            # 关联标签
            tags = article_data.get('tags', [])
            for tag_name in tags:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'color': '#1890ff'}
                )
                post.tags.add(tag)

            # 处理图片
            images = article_data.get('images', [])
            for img_data in images:
                self._process_image(post, img_data, data_dir)

            created_count += 1
            self.stdout.write(f'  创建文章: {title[:40]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('导入完成！'))
        self.stdout.write(f'  新增: {created_count} 篇')
        self.stdout.write(f'  跳过: {skipped_count} 篇')

    def _resolve_author(self, author_id):
        if author_id:
            author = User.objects.filter(id=author_id).first()
            if not author:
                self.stdout.write(self.style.ERROR(f'作者 ID {author_id} 不存在'))
            return author

        author = User.objects.filter(email=DEFAULT_AUTHOR_EMAIL).first()
        if not author:
            self.stdout.write(self.style.ERROR(
                f'默认作者 {DEFAULT_AUTHOR_EMAIL} 不存在，请用 --author-id 指定'
            ))
        return author

    def _process_image(self, post, img_data, data_dir):
        img_file = img_data.get('file', '')
        if not img_file:
            return

        img_path = data_dir / img_file
        if not img_path.exists():
            self.stdout.write(self.style.WARNING(f'  图片不存在: {img_path}'))
            return

        with open(img_path, 'rb') as f:
            processed = process_image(
                f,
                max_width=1200,
                max_height=1200,
                quality=85,
                convert_webp=True,
            )

        base_name = os.path.splitext(os.path.basename(img_file))[0]
        new_name = f'{base_name}_compressed.webp'

        processed_image = InMemoryUploadedFile(
            file=processed,
            field_name='image',
            name=new_name,
            content_type='image/webp',
            size=processed.getbuffer().nbytes,
            charset=None,
        )

        PostImage.objects.create(
            post=post,
            image=processed_image,
            alt=img_data.get('alt', ''),
            order=img_data.get('order', 0),
        )
