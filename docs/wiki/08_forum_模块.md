## 8. forum 模块

### 8.1 模块职责

论坛核心：帖子发布（Markdown + 图片延迟关联）、树形评论（点赞/点踩）、标签、收藏、举报、热度排行、统计字段冗余 + Redis 浏览量缓存。

### 8.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/models.py)）

| 模型              | db\_table          | 核心设计                                                                                   |
| --------------- | ------------------ | -------------------------------------------------------------------------------------- |
| **Tag**         | `forum_tag`        | name unique、color、use\_count 冗余计数                                                      |
| **PostTag**     | `forum_post_tags`  | 自定义中间表，`unique_together=['post','tag']`                                                |
| **Post**        | `forum_post`       | 软删除（status='deleted'）、冗余统计（view\_count/like\_count/comment\_count/collect\_count）、复合索引 |
| **Comment**     | `forum_comment`    | 树形 parent 自关联、软删除（is\_deleted）、is\_hidden 管理员隐藏                                        |
| **PostLike**    | —                  | `unique_together=['post','user']`（幂等）                                                  |
| **CommentLike** | —                  | `unique_together=['comment','user']`、`is_like` Bool 区分赞/踩                              |
| **PostCollect** | —                  | `unique_together=['post','user']`                                                      |
| **Report**      | —                  | 通用举报：content\_type CharField + object\_id（不用 ContentType）                              |
| **PostImage**   | `forum_post_image` | **post 允许 null（延迟关联）**、`upload_to='forum/posts/%Y/%m/'`                                |

#### Post 字段（[L81-L178](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/models.py#L81-L178)）

| 字段                                                          | 类型             | 说明                               |
| ----------------------------------------------------------- | -------------- | -------------------------------- |
| title                                                       | CharField(200) | db\_index, MinLengthValidator(3) |
| content / content\_md                                       | TextField      | 正文 + Markdown 源码                 |
| author                                                      | FK→User        | CASCADE, related\_name='posts'   |
| view\_count / like\_count / comment\_count / collect\_count | IntegerField   | **冗余统计字段**（用 F 表达式原子更新）          |
| is\_pinned / is\_essence / is\_closed                       | BooleanField   | 置顶/精华/关闭评论                       |
| status                                                      | CharField(20)  | choices: published/deleted/draft |
| tags                                                        | M2M(Tag)       | through='PostTag'                |
| report\_count                                               | IntegerField   | 举报数                              |
| created\_at / updated\_at                                   | DateTimeField  | <br />                           |

- **软删除**：`soft_delete()` → `save(update_fields=['status'])`
- **Meta ordering**：`['-is_pinned', '-is_essence', '-created_at']`
- **复合索引**：`[author, -created_at]`、`[-created_at]`、`[status, -created_at]`

### 8.3 URL 路由表（[urls.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/urls.py)）

`DefaultRouter` 注册：

| 路由                        | 视图                         | 方法                   | 权限                        | 功能                               |
| ------------------------- | -------------------------- | -------------------- | ------------------------- | -------------------------------- |
| `/posts/`                 | PostViewSet                | GET                  | IsAuthenticatedOrReadOnly | 帖子列表（search/ordering/filter/hot） |
| `/posts/{id}/`            | PostViewSet                | GET/PUT/PATCH/DELETE | + IsOwnerOrReadOnly       | 详情（retrieve 自动 +1 浏览量）           |
| `/posts/{id}/like/`       | PostViewSet\@like          | POST                 | IsAuthenticated           | 切换点赞                             |
| `/posts/{id}/collect/`    | PostViewSet\@collect       | POST                 | IsAuthenticated           | 切换收藏                             |
| `/posts/{id}/comments/`   | PostViewSet\@comments      | GET                  | IsAuthenticatedOrReadOnly | 帖子一级评论                           |
| `/posts/my_posts/`        | PostViewSet\@my\_posts     | GET                  | IsAuthenticated           | 当前用户帖子                           |
| `/posts/collected/`       | PostViewSet\@collected     | GET                  | —                         | 当前用户收藏                           |
| `/posts/hot/`             | PostViewSet\@hot           | GET                  | —                         | 热门帖子                             |
| `/posts/upload_image/`    | PostViewSet\@upload\_image | POST                 | IsAuthenticated           | 上传图片（post=None 延迟关联）             |
| `/comments/`              | CommentViewSet             | GET                  | IsAuthenticatedOrReadOnly | 一级评论列表                           |
| `/comments/{id}/like/`    | CommentViewSet\@like       | POST                 | —                         | 评论点赞                             |
| `/comments/{id}/dislike/` | CommentViewSet\@dislike    | POST                 | —                         | 评论点踩                             |
| `/tags/`                  | TagViewSet                 | GET                  | IsAuthenticatedOrReadOnly | 标签（只读）                           |
| `/reports/`               | ReportViewSet              | GET/POST             | IsAuthenticated           | 举报（管理员看全部）                       |

### 8.4 视图说明（[views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py)）

#### PostViewSet（[L31-L441](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L31-L441)）

- 继承 `ModelViewSet`
- queryset：`Post.objects.filter(status='published').select_related('author').prefetch_related('tags', 'images')`
- permission：`[IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]`

**过滤器配置**：

- `filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]`
- `search_fields = ['title', 'content']`
- `ordering_fields = ['created_at', 'view_count', 'like_count', 'comment_count', 'is_pinned', 'is_essence']`
- `ordering = ['-is_pinned', '-is_essence', '-created_at']`
- `filterset_fields = ['tags__name', 'is_pinned', 'is_essence', 'created_at']`

**关键方法**：

- `get_serializer_class()`：list → PostListSerializer；create/update → PostCreateUpdateSerializer；其他 → PostSerializer
- `list()`（[L82-L118](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L82-L118)）：`hot` 参数存在时 `annotate(hot_score=Count('likes')*3 + Count('comments')*2 + Count('collects'))` + `order_by('-hot_score')`
- `retrieve()`：调 `PostCacheService.increase_view(id)`
- `destroy()`：`instance.soft_delete()`
- `update()`：手动检查 `instance.author != request.user` → 403
- `like` action：`PostInteractionService.toggle_like` → `{liked, like_count}`
- `collect` action：`toggle_collect`
- `comments` action：**只返回一级评论**（`parent=None`）
- `hot` action：支持 days（默认7）、limit（默认20）→ `HotPostService.get_hot_posts`
- `upload_image` action（[L378-L441](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L378-L441)）：
  - 校验 content\_type（jpeg/jpg/png/gif/webp）+ 大小 ≤ 5MB
  - `process_image(max_width=1200, max_height=1200, quality=85, crop_square=, convert_webp=True)`
  - 创建 `PostImage(post=None)` **延迟关联**

#### CommentViewSet（[L444-L577](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/views.py#L444-L577))

- 继承 `ModelViewSet`
- `get_queryset()`：list 动作 → `filter(parent=None)` **只返回一级评论** + `order_by('-created_at')`
- `create/destroy`：手动重算 `post.comment_count`
- `like`/`dislike` action：`PostInteractionService.toggle_comment_reaction(comment_id, user, is_like=True/False)`

### 8.5 序列化器（[serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/serializers.py)）

| 序列化器                         | 用途      | 关键设计                                                  |
| ---------------------------- | ------- | ----------------------------------------------------- |
| `TagSerializer`              | 标签      | id/name/color/use\_count                              |
| `PostImageSerializer`        | 帖子图片    | `image_url` SerializerMethodField → `build_image_url` |
| `PostListSerializer`         | 帖子列表    | 嵌套 author/tags，`get_images` 最多 4 张预览图                 |
| `PostSerializer`             | 帖子详情    | 动态字段 `is_liked`/`is_collected`，write\_only `tag_ids`  |
| `PostCreateUpdateSerializer` | 创建/更新   | 支持 .md 文件上传；`_sync_post_images` 全量同步图片                |
| `ReplySerializer`            | 子评论（轻量） | 不含 replies 避免递归；`liked`/`disliked`/`reply_to_name`    |
| `CommentSerializer`          | 一级评论    | `get_replies` **深度优先递归扁平化**所有子孙；`reply_count`         |
| `ReportSerializer`           | 举报      | reporter 自动设当前用户                                      |

#### \_sync\_post\_images 全量同步逻辑（[L389-L436](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/serializers.py#L389-L436)）

1. `re.findall(r'!\[.*?\]\((.*?)\)', content)` 解析 Markdown 所有图片 URL
2. 收集当前 `post.images.all()` 的 `image.name` → `existing_images`
3. 筛选 URL 包含 `/media/forum/posts/` 或 `/media/formulas/` 的，提取 `image_path = url.split('/media/')[-1]` → `required_images`
4. **删除多余**：已关联但不在 Markdown 中的 → `img.delete()`
5. **补齐缺失**：Markdown 中存在但未关联且文件存在的 → `PostImage.objects.create`

### 8.6 服务层（[services.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py)）

> ⚠️ **违反项目规则**：[L16, L23-25](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L16-L25) 使用内置 `logging` 模块，应改用 loguru。

#### PostCacheService（[L28-L177](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L28-L177)）

**缓存键**：`forum:post:{post_id}:view`

| 方法                        | 逻辑                                                                                                                                        |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `increase_view(post_id)`  | 优先 `cache.incr(key)`；异常降级查库 + `F('view_count')+1` + `save(update_fields=['view_count'])`                                                  |
| `get_view_count(post_id)` | `cache.get` 命中返回；未命中查库 + `cache.set(key, count, 3600)`                                                                                    |
| `sync_all_views()`        | ⚠️ **使用 KEYS 命令** `con.keys("*forum:post:*:view")`（阻塞风险，建议改 SCAN）；解析 post\_id 后 `update(view_count=F('view_count')+int(views))`；删除已同步 key |

#### PostInteractionService（[L180-L345](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L180-L345)）

| 方法                                                   | 逻辑                                                              |
| ---------------------------------------------------- | --------------------------------------------------------------- |
| `toggle_like(post_id, user)`                         | 已赞：delete + `F('like_count')-1`；未赞：create + `F('like_count')+1` |
| `toggle_collect(post_id, user)`                      | 对称收藏切换                                                          |
| `toggle_comment_reaction(comment_id, user, is_like)` | 三态：新建反应 / 取消反应 / 切换反应（赞↔踩）                                      |

#### HotPostService（[L348-L389](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/services.py#L348-L389)）

`get_hot_posts(days=7, limit=20)`：

- **热度算法**：`hot_score = F('like_count')*3 + F('comment_count')*2 + F('view_count')`
- 权重：点赞×3（认可度）、评论×2（参与度）、浏览×1（防刷量）
- `annotate + order_by('-hot_score')[:limit]`

### 8.7 权限类（[permissions.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/permissions.py)）

| 权限类                        | 逻辑                                                                         |
| -------------------------- | -------------------------------------------------------------------------- |
| `IsPostOwnerOrReadOnly`    | 读放行；写检查 `obj.author == request.user`                                       |
| `IsCommentOwnerOrReadOnly` | 同上                                                                         |
| `CanModeratePost`          | has\_permission: is\_staff or is\_moderator；has\_object\_permission: 放宽至作者 |

> 注：PostViewSet 实际复用 accounts 的 `IsOwnerOrReadOnly`，未使用 forum 自身权限类（预留）。

### 8.8 信号（[signals.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/forum/signals.py)）

| 信号           | sender  | 接收器                                   | 逻辑                                                    |
| ------------ | ------- | ------------------------------------- | ----------------------------------------------------- |
| post\_save   | Comment | `update_post_comment_count`           | `created and not is_deleted` 时重算 `post.comment_count` |
| post\_delete | Comment | `update_post_comment_count_on_delete` | 物理删除时重算 comment\_count                                |
| post\_save   | Tag     | `update_tag_use_count`                | `use_count = instance.posts.count()`                  |

> ⚠️ CommentViewSet.create/destroy 也手动更新 comment\_count，与信号存在重复。

### 8.9 帖子图片关联机制

采用**全量同步模式**：

```
用户上传图片(upload_image action)
    ↓ PostImage(post=None) 延迟关联存储
用户提交帖子(content 含 Markdown)
    ↓ _sync_post_images(post, content)
    ├── 解析 Markdown ![](url) 提取 required_images
    ├── 删除 post.images 中不在 required_images 的
    └── 为 required_images 中未关联的创建 PostImage(post=post)
```

支持两类图片来源：用户上传 `/media/forum/posts/` + 公式库 `/media/formulas/`（跨模块引用 formula 应用图片）。

### 8.10 management/commands

| 命令 | 功能 |
| --- | --- |
| `import_articles` | 从 JSON 数据包导入文章（含图片压缩 + WebP 转换）；参数：`<data_dir>`（含 articles.json 和 images/）、`--author-id N`（默认 `baihao6340@163.com`）、`--force`（删除同标题旧文后重新导入） |

***
