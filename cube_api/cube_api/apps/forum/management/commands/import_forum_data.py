# apps/forum/management/commands/import_forum_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.forum.models import Tag, Post, Comment
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = '导入论坛基础数据（标签、示例帖子等）'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始导入论坛数据...'))

        # 1. 导入标签
        self.import_tags()

        # 2. 创建测试用户（如果需要）
        self.create_test_users()

        # 3. 导入示例帖子
        self.import_sample_posts()

        self.stdout.write(self.style.SUCCESS('论坛数据导入完成！'))

    def import_tags(self):
        """导入标签数据"""
        tags_data = [
            {'name': 'CFOP', 'color': '#409EFF', 'use_count': 0},
            {'name': '三阶', 'color': '#67C23A', 'use_count': 0},
            {'name': '新手', 'color': '#E6A23C', 'use_count': 0},
            {'name': '进阶', 'color': '#F56C6C', 'use_count': 0},
            {'name': '四阶', 'color': '#909399', 'use_count': 0},
            {'name': '高阶', 'color': '#9C27B0', 'use_count': 0},
            {'name': '二阶', 'color': '#FF9800', 'use_count': 0},
            {'name': '公式', 'color': '#00BCD4', 'use_count': 0},
            {'name': '技巧', 'color': '#795548', 'use_count': 0},
            {'name': '比赛', 'color': '#FF5722', 'use_count': 0},
        ]

        created_count = 0
        for tag_data in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_data['name'],
                defaults={
                    'color': tag_data['color'],
                    'use_count': tag_data['use_count']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ 创建标签: {tag.name}')
            else:
                self.stdout.write(f'  ⏭️ 标签已存在: {tag.name}')

        self.stdout.write(self.style.SUCCESS(f'标签导入完成，新增 {created_count} 个'))

    def create_test_users(self):
        """创建测试用户"""
        users_data = [
            {'email': 'user1@example.com', 'password': 'test123', 'username': '魔方小白'},
            {'email': 'user2@example.com', 'password': 'test123', 'username': '速拧大神'},
            {'email': 'user3@example.com', 'password': 'test123', 'username': '公式收藏家'},
        ]

        created_count = 0
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'username': user_data['username'],
                    'bio': f'魔方爱好者，欢迎交流！'
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                created_count += 1
                self.stdout.write(f'  ✅ 创建用户: {user.username} ({user.email})')
            else:
                self.stdout.write(f'  ⏭️ 用户已存在: {user.username}')

        self.stdout.write(self.style.SUCCESS(f'用户导入完成，新增 {created_count} 个'))

    def import_sample_posts(self):
        """导入示例帖子"""
        # 获取用户
        try:
            author = User.objects.get(email='user1@example.com')
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('  ⚠️ 未找到测试用户，跳过示例帖子导入'))
            return

        # 获取标签
        cfop_tag = Tag.objects.filter(name='CFOP').first()
        sanjie_tag = Tag.objects.filter(name='三阶').first()
        xinshou_tag = Tag.objects.filter(name='新手').first()

        posts_data = [
            {
                'title': '【新手必看】三阶魔方零基础入门教程',
                'content': '''# 三阶魔方零基础入门教程

## 前言
魔方并不难，只要掌握了方法，任何人都可以学会还原三阶魔方。

## 第一步：底层十字
在底面拼出一个白色十字，且棱块侧面颜色与中心块对齐。

## 第二步：底层角块
完成白色面，同时底层四周颜色对齐。

## 第三步：中层棱块
还原第二层（中间层）的四个棱块。

## 第四步：顶层十字
在顶层拼出黄色十字。

## 第五步：顶层面位
将顶层全部变成黄色。

## 第六步：顶层角块归位
调整顶层角块位置。

## 第七步：顶层棱块归位
最后一步，完成整个魔方！

祝大家早日学会魔方！🎉''',
                'tags': [xinshou_tag, sanjie_tag] if xinshou_tag and sanjie_tag else [],
                'is_pinned': True,
                'is_essence': True
            },
            {
                'title': 'CFOP速拧教程 - F2L理解法',
                'content': '''# CFOP进阶教程：F2L理解法

## 什么是F2L？
F2L（First Two Layers）是CFOP速拧法的第二步，指同时还原前两层。

## 核心思想
F2L的本质是把一对"角块+棱块"组合起来放入正确的位置。

## 常用F2L公式

| 情况 | 公式 |
|------|------|
| 角棱相连 | `U R U' R'` |
| 角棱分离 | `R U R'` |
| 角棱背面 | `R U2 R' U R U R'` |

## 练习技巧
1. 慢速练习，理解原理
2. 找规律，观察相对位置
3. 预判下一组

F2L熟练后，成绩可轻松进入30秒！💪''',
                'tags': [cfop_tag, sanjie_tag] if cfop_tag and sanjie_tag else [],
                'is_pinned': False,
                'is_essence': True
            },
            {
                'title': '魔方公式记忆技巧分享',
                'content': '''# 魔方公式记忆技巧

## 肌肉记忆法
不要死记硬背公式字母，而是通过反复练习形成肌肉记忆。

## 分段记忆
将长公式分成几个小段，逐段练习后连接。

## 镜像对称
很多公式是左右对称的，记住一个就能推导出另一个。

## 故事联想
为公式中的转动编一个故事，帮助记忆。

## 每天10分钟
坚持每天练习，比一次性练很久效果更好。

大家有什么好的记忆方法？欢迎分享！''',
                'tags': [cfop_tag] if cfop_tag else [],
                'is_pinned': False,
                'is_essence': False
            }
        ]

        created_count = 0
        for post_data in posts_data:
            # 检查是否已存在
            if Post.objects.filter(title=post_data['title']).exists():
                self.stdout.write(f'  ⏭️ 帖子已存在: {post_data["title"][:30]}...')
                continue

            tags = post_data.pop('tags')
            post = Post.objects.create(
                title=post_data['title'],
                content=post_data['content'],
                author=author,
                is_pinned=post_data.get('is_pinned', False),
                is_essence=post_data.get('is_essence', False)
            )
            if tags:
                post.tags.set(tags)
            created_count += 1
            self.stdout.write(f'  ✅ 创建帖子: {post.title[:30]}...')

        self.stdout.write(self.style.SUCCESS(f'帖子导入完成，新增 {created_count} 个'))