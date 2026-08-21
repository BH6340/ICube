# ICube 魔方学习网站项目总结

## 项目概述

ICube 是一个面向魔方爱好者的学习交流网站，提供公式学习、3D魔方可视化、计时练习、教程学习、社区论坛、商城购物等功能。项目采用前后端分离架构，后端基于 Python Django，前端基于 Vue 3，支持 Docker 容器化部署。

---

## 技术架构

### 后端 (cube_api)

| 技术栈       | 版本/说明                              |
| ------------ | -------------------------------------- |
| **框架**     | Django 6.0 + Django REST Framework     |
| **数据库**   | MySQL 8.0（开发/生产）+ SQLite（测试） |
| **缓存**     | Redis 7                                |
| **认证**     | JWT (djangorestframework-simplejwt)    |
| **API 文档** | drf-spectacular (Swagger/Redoc)        |
| **限流**     | DRF Throttling                         |
| **跨域**     | django-cors-headers                    |
| **筛选**     | django-filter                          |
| **图片处理** | Pillow（压缩/裁剪/WebP转换）           |
| **日志**     | loguru                                 |

### 前端 (cube_front)

| 技术栈         | 版本/说明                |
| -------------- | ------------------------ |
| **框架**       | Vue 3.5 + Vite 8.0       |
| **状态管理**   | Pinia 3.0                |
| **路由**       | Vue Router 5.0           |
| **UI 组件**    | Element Plus 2.14        |
| **3D 渲染**    | Three.js 0.184           |
| **HTTP 请求**  | Axios 1.16               |
| **富文本编辑** | Quill (@vueup/vue-quill) |

---

## 项目结构

### 后端目录结构

```
cube_api/
├── cube_api/                    # Django 项目配置
│   ├── apps/                    # 应用模块
│   │   ├── accounts/            # 用户管理
│   │   │   ├── models.py        # 自定义 User 模型（关注关系、Redis缓存）
│   │   │   ├── views.py         # 注册、登录、关注、资料管理
│   │   │   ├── authentication.py # CachedJWTAuthentication
│   │   │   ├── services.py      # ProfileCacheService, JWTCacheService
│   │   │   └── throttles.py     # 登录限流
│   │   ├── forum/               # 论坛系统
│   │   │   ├── models.py        # Post, Comment, Tag, Like, Collect, Report, PostImage
│   │   │   ├── views.py         # 帖子CRUD、点赞、收藏、评论、热门排行、图片上传
│   │   │   ├── services.py      # PostCacheService, HotPostService
│   │   │   ├── serializers.py   # PostImageSerializer、图片URL动态生成
│   │   │   └── permissions.py   # IsOwnerOrReadOnly
│   │   ├── home/                # 首页导航
│   │   │   ├── models.py        # NavigationMenu、Banner轮播图
│   │   │   ├── views.py         # BannerViewSet
│   │   │   ├── serializers.py   # BannerSerializer（图片URL动态生成）
│   │   │   ├── admin.py         # BannerAdmin（图片预览、状态Badge）
│   │   │   └── urls.py          # 轮播图API路由
│   │   ├── formula/             # 公式库系统
│   │   │   ├── models.py        # CubeCategory, CubeState, Formula, FormulaTag, FormulaCollection
│   │   │   ├── views.py         # 公式CRUD、收藏管理、筛选搜索排序、浏览量统计、作者列表接口
│   │   │   ├── serializers.py   # 公式序列化器（支持thumbnail_file/thumbnail_path双字段）
│   │   │   ├── filters.py       # 公式筛选器（难度多选、作者筛选）
│   │   │   ├── permissions.py   # IsAdminOrReadOnly, IsAdminOrCustomCreator
│   │   │   ├── services.py      # FormulaMatchService（公式匹配）
│   │   │   └── urls.py          # 公式API路由
│   │   ├── shop/                # 商城系统
│   │   │   ├── models.py        # Product, Cart, Order, OrderItem
│   │   │   ├── views.py         # 商品CRUD、购物车、订单管理
│   │   │   ├── serializers.py   # 商城序列化器
│   │   │   ├── alipay_config.py # 支付宝支付配置
│   │   │   └── keys/            # 支付宝密钥文件
│   │   └── timer/               # 计时器模块
│   │       ├── models.py        # TimerRecord
│   │       ├── views.py         # 计时记录CRUD
│   │       └── serializers.py   # 计时器序列化器
│   ├── utils/                   # 工具类
│   │   ├── common_response.py   # 统一 API 响应格式
│   │   ├── common_exception.py  # 统一异常处理
│   │   ├── common_pagination.py # 统一分页
│   │   ├── image_url.py         # 图片URL统一生成（默认返回相对路径）
│   │   └── image_processor.py   # 图片处理工具（压缩、裁剪、WebP转换、缩略图生成）
│   └── settings/                # 配置文件
│       ├── dev.py               # 开发环境配置
│       ├── prod.py              # 生产环境配置
│       └── logger_conf.py       # 日志配置
├── media/                       # 媒体文件（头像、公式缩略图）
│   ├── avatars/                 # 用户头像
│   ├── formulas/                # 公式图片（F2L/OLL/PLL）
│   └── forum/                   # 论坛帖子图片
├── scripts/                     # 辅助脚本
│   ├── import_formulas.py       # 公式导入
│   ├── regenerate_inverse.py    # 逆公式生成
│   └── update_difficulty.py     # 难度更新
└── manage.py                    # Django 管理命令
```

### 前端目录结构

```
cube_front/
├── src/
│   │   ├── components/              # 组件
│   │   │   ├── formula/             # 公式相关组件
│   │   │   │   ├── CubeDemo.vue     # Three.js 3D魔方动画演示
│   │   │   │   ├── FormulaLibrary.vue # 公式库卡片列表（分类/筛选/搜索/详情弹窗/作者筛选）
│   │   │   │   └── FormulaEditor.vue # 公式编辑器组件（上传/编辑公式）
│   │   │   ├── forum/               # 论坛组件
│   │   │   │   ├── CommentSection.vue # 评论区
│   │   │   │   ├── MarkdownEditor.vue # Markdown编辑器
│   │   │   │   └── TagSelector.vue  # 标签选择器
│   │   │   ├── ImageCropper.vue     # 图片裁剪组件（1:1比例、滚轮缩放、防抖拖拽）
│   │   │   ├── Header.vue           # 顶部导航栏
│   │   ├── Footer.vue           # 页脚
│   │   └── Main.vue             # 首页主内容（轮播图、精选公式、教程入口）
│   ├── views/                   # 页面视图
│   │   ├── HomeView.vue         # 首页布局
│   │   ├── TutorialView.vue     # 教程页
│   │   ├── FormulaView.vue      # 公式页（包含公式库）
│   │   ├── TimerView.vue        # 计时器页
│   │   ├── ShopView.vue         # 商城页
│   │   ├── CartView.vue         # 购物车页
│   │   ├── CheckoutView.vue     # 结算页
│   │   ├── PayView.vue          # 支付页
│   │   ├── LoginView.vue        # 登录页
│   │   ├── RegisterView.vue     # 注册页
│   │   ├── forum/               # 论坛页面
│   │   │   ├── ForumView.vue    # 论坛列表
│   │   │   ├── PostDetailView.vue # 帖子详情
│   │   │   └── PostEditorView.vue # 发帖/编辑
│   │   ├── profiles/            # 个人中心
│   │   │   ├── InfoView.vue     # 个人信息（关注/粉丝/收藏统计）
│   │   │   ├── CollectionView.vue # 公式收藏页（分类/筛选/搜索）
│   │   │   └── OrderView.vue    # 订单列表页
│   │   └── tutorial/            # 教程页面
│   │       ├── BeginnerTutorial.vue # 层先法教程（7步骤）
│   │       ├── CFOPTutorial.vue # CFOP教程（十字/F2L/OLL/PLL）
│   │       ├── OLLEssentials.vue # OLL基础教程（两步OLL：10个算法）
│   │       ├── PLLEssentials.vue # PLL基础教程（两步PLL：6个算法）
│   │       ├── CompleteOLL.vue  # 完整OLL教程（57个算法）
│   │       └── CompletePLL.vue  # 完整PLL教程（21个算法）
│   ├── stores/                  # Pinia 状态管理
│   │   ├── user.js              # 用户状态
│   │   └── menu.js              # 菜单状态
│   ├── api/                     # API 接口封装
│   │   ├── user.js              # 用户接口
│   │   ├── posts.js             # 帖子接口
│   │   ├── comments.js          # 评论接口
│   │   ├── tags.js              # 标签接口
│   │   ├── home.js              # 首页接口
│   │   ├── formula.js           # 公式接口（分类/列表/收藏）
│   │   ├── shop.js              # 商城接口（商品/购物车/订单）
│   │   └── timer.js             # 计时器接口
│   ├── http/                    # HTTP 配置
│   │   └── request.js           # Axios 请求封装（含代理配置、401自动清除登录态）
│   └── router/index.js          # 路由配置（含教程路由）
├── public/                      # 静态资源
├── scripts/                     # 辅助脚本
│   └── CubeTest.html            # 3D魔方测试页面
└── package.json                 # 依赖配置
```

### 项目根目录脚本

```
ICube/
├── dev-local.ps1                # 本地开发一键启停脚本（PowerShell，不纳入 Git）
├── deploy.sh                    # 服务器一键部署脚本（Bash）
├── docker-compose.yml           # Docker Compose 编排配置
└── .env                         # 生产环境变量（不纳入 Git）
```

---

## 核心功能

### 1. 用户系统
- **注册/登录**：支持邮箱+密码认证，登录限流保护
- **用户资料**：自定义头像、个人简介
- **关注系统**：支持关注/取消关注，Redis 缓存粉丝/关注数量
- **JWT 认证**：Token 黑名单机制，退出登录即时失效
- **收藏统计**：个人中心显示公式收藏数量

### 2. 论坛系统
- **帖子管理**：发布、编辑、软删除、置顶、精华标识
- **评论系统**：支持多级回复、点赞、点踩
- **图片上传**：支持多图上传，自动关联到帖子，使用独立上传接口获取实际URL
- **图片预览**：帖子列表显示内容中的图片预览，支持左右布局（左侧内容、右侧1:1比例图片）
- **图片全量同步**：编辑帖子时从Markdown内容解析所有图片，自动同步数据库关联
- **互动功能**：帖子点赞、收藏
- **热门排行**：基于点赞、评论、收藏计算热度
- **标签系统**：帖子标签分类
- **举报功能**：支持举报帖子和评论

### 3. 魔方公式库
- **公式分类**：按魔方阶数、解法（如 CFOP）、阶段（F2L/OLL/PLL）分类
- **自定义分类**：支持用户创建自定义公式分类，分类包含阶数、求解方法、阶段字段
- **分类权限**：普通用户只能看到系统分类 + 自己的自定义分类，支持分类的创建和删除
- **公式状态**：支持配置公式目标状态（用于3D演示）
- **公式展示**：公式名称、记号、逆公式、缩略图、浏览量
- **难度分级**：基础（≤6步）、进阶（7-11步）、困难（≥12步）
- **搜索筛选**：支持按分类、难度、作者筛选，按名称/记号搜索，支持多重筛选
- **公式收藏**：收藏/取消收藏，个人中心展示收藏列表
- **3D 演示**：点击公式卡片查看3D动画演示，支持自动播放公式步骤
- **3D 重置**：重置时自动恢复初始视角（相机位置+目标点Tween动画）
- **浏览量统计**：公式详情页访问自动递增 `view_count`，使用 F 表达式原子更新
- **公式跳转**：首页精选公式点击后自动跳转到公式库并打开对应公式详情弹窗
- **用户上传公式**：支持用户自定义上传公式，公式所有人可见
- **作者筛选**：支持按作者筛选公式，作者字段自动关联当前用户
- **公式编辑器**：支持公式名称、记号、分类、难度、图片等信息的编辑，支持从系统分类和自定义分类中选择
- **公式记号输入**：支持点击式键盘输入（R/L/U/D/F/B/r/l/u/d/f/b/M/E/S/x/y/z等），也支持直接输入字符串
- **图片来源**：可从公式库选择图片或自己上传图片
- **图片处理**：上传时自动压缩（>2048px先缩小）、1:1比例裁剪、转换为WebP格式
- **图片裁剪组件**：支持滚轮缩放、防抖拖拽、实时预览裁剪框
- **自动缩略图**：无图片时自动生成包含公式名称和记号的缩略图
- **目标状态绑定**：创建/编辑公式时自动根据分类绑定目标状态
- **权限控制**：管理员可编辑所有公式，普通用户仅可编辑自己上传的公式
- **逆公式生成**：自动生成公式的逆公式用于3D演示回退，修改公式时逆公式同步更新
- **自定义分类弹窗**：创建公式时可通过弹窗创建自定义分类，支持选择阶数、求解方法、阶段
- **公式卡片优化**：公式卡片头部显示公式名+难度标签，底部显示"分类名  by 用户名"格式；公式名、分类名、作者名使用相同字体大小和样式，中间用两个空格隔开；用户上传的自定义公式可在"我的公式"页面进行编辑和删除
- **公式删除**：用户可删除自己创建的自定义公式

### 4. 教程系统
- **层先法教程**：7个完整步骤（对好第一面十字、对好第一面加T字形、对好前两层、在黄色顶面画十字、对好顶层黄色面、调整顶层角块位置、调整顶层棱块位置）
- **CFOP教程**：包含十字、F2L、OLL、PLL四个阶段的详细教程
- **OLL基础教程**：两步OLL学习路径，包含3种棱块定向和7种角块定向（共10个算法）
- **PLL基础教程**：两步PLL学习路径，包含2种角块排列和4种棱块排列（共6个算法）
- **完整OLL教程**：57个OLL算法的分组学习指南
- **完整PLL教程**：21个PLL算法的分组学习指南
- **学习路径**：初学者路径（16个算法，1-2周学会）和进阶路径（78个算法，达到sub-20秒）
- **教程导航优化**：教程列表页包含学习路径流程图、热门教程卡片、CFOP进阶课程分类，各教程页面之间互相导航，形成完整的学习链路

### 5. 商城系统
- **商品管理**：商品列表、分类、详情展示
- **购物车**：添加商品、修改数量、删除商品
- **订单管理**：创建订单、订单列表、订单详情
- **支付宝支付**：集成支付宝支付接口，支持支付回调
- **订单状态**：待支付、已支付、已发货、已完成

### 6. 计时器
- **计时功能**：精确毫秒级计时，支持单次计时和多次计时
- **记录保存**：计时记录自动保存到数据库
- **成绩统计**：平均成绩、最佳成绩统计

### 7. 3D 魔方可视化
- **Three.js 渲染**：基于 Three.js 实现可交互的 3D 魔方
- **旋转动画**：支持单层、双层（小写记号）、中间层、整体旋转
- **状态渲染**：根据公式目标状态渲染魔方颜色
- **公式播放**：自动播放公式步骤，展示执行过程

### 8. 首页导航
- **动态菜单**：菜单数据从数据库读取，支持主导航和个人中心导航
- **精选公式**：展示浏览量最高的公式，支持点击跳转
- **教程入口**：层先法教程、CFOP教程卡片入口
- **轮播图系统**：支持后台动态管理轮播图，包含标题、描述、图片、跳转链接、排序、状态管理，前端支持渐变遮罩层、悬停暂停、图片加载占位符等交互效果

---

## 技术亮点

### 后台管理 (django-unfold)

项目使用 `django-unfold` 作为后台管理框架，提供现代化的 Tailwind CSS 风格管理界面，替代原生 Django Admin。

**核心特性**：
- **统一继承**：所有 Admin 类继承自 `unfold.admin.ModelAdmin`
- **@display 装饰器**：自定义列表页列，支持 Badge 标签、图片预览等
- **@action 装饰器**：定义批量操作，支持管理员高效运维
- **Fieldsets 分组**：编辑页按逻辑分组展示字段
- **侧边栏自定义**：支持中文标题、可折叠分组、自定义排序

**各应用 Admin 配置**：

| 应用 | Admin类 | 特色功能 |
|------|---------|----------|
| accounts | UserAdmin | 头像预览、状态Badge、密码安全提示、批量禁用/解冻 |
| forum | PostAdmin | 状态Badge、置顶/精华标记、批量置顶/加精/软删除 |
| forum | ReportAdmin | 举报原因Badge、内容类型Badge、批量处理/驳回 |
| shop | ProductAdmin | 缩略图预览、库存状态Badge、批量上架/下架 |
| shop | OrderAdmin | 订单状态Badge、批量发货/完成、时间层级导航 |
| formula | FormulaAdmin | 公式缩略图预览、难度分级展示 |
| home | NavigationMenuAdmin | 菜单排序、层级管理、分类Badge |
| home | BannerAdmin | 图片预览、状态Badge、列表页可编辑排序和状态、批量启用/禁用 |
| timer | TimerRecordAdmin | 计时记录管理 |

**侧边栏配置**：
- 按指定顺序排列：认证和授权 → Home → Accounts → 论坛 → 魔方公式 → Timer → 商城
- 子目录点击展开，支持折叠
- 一级目录标题字体更大（16px），子目录保持默认大小（14px）

**模板覆盖**：
- 通过项目 `templates/unfold/helpers/app_list.html` 覆盖 unfold 包内模板，修改一级目录字体大小

### 后端优化
1. **Redis 缓存**：粉丝/关注数量缓存、帖子浏览量缓存、JWT 黑名单
2. **统一响应格式**：`APIResponse` 统一封装
3. **限流保护**：登录接口限流、全局限流
4. **软删除**：帖子和评论支持软删除
5. **权限控制**：自定义 `IsOwnerOrReadOnly`、`IsAdminOrCustomCreator` 权限类
6. **公式筛选**：使用 django-filter 实现难度多选筛选、作者筛选
7. **逆公式生成**：自动生成公式的逆公式用于3D演示回退
8. **图片URL统一管理**：通过 `build_image_url()` 函数统一生成图片URL，默认返回相对路径避免CORS问题，支持 `absolute` 参数生成完整URL（用于邮件等场景）
9. **浏览量原子更新**：使用 `F('view_count') + 1` 表达式实现浏览量的原子递增
10. **图片处理流水线**：使用 Pillow 实现图片压缩（>2048px自动缩小）、1:1比例裁剪、WebP格式转换、质量优化
11. **公式图片双字段**：`thumbnail_file`（用户上传文件，经压缩裁剪处理）和 `thumbnail_path`（公式库图片路径引用），分别处理不同图片来源
12. **自动缩略图生成**：无上传图片时，根据公式名称和记号自动生成缩略图
13. **目标状态自动绑定**：创建/编辑公式时根据分类自动查找并绑定对应的目标状态
14. **JWT认证兼容**：`CachedJWTAuthentication` 验证失败返回 None 而非抛出异常，兼容 `IsAuthenticatedOrReadOnly` 权限

### 前端特性
1. **3D 魔方渲染**：Three.js 实现魔方旋转动画和状态渲染，重置时视角Tween动画复原
2. **响应式导航**：根据路由自动切换菜单高亮
3. **状态管理**：Pinia 管理用户和菜单状态
4. **路由守卫**：部分页面需要登录权限
5. **公式库交互**：分类树、难度筛选、作者筛选、搜索框、排序选择、分页、详情弹窗
6. **收藏同步**：公式库和收藏页收藏状态实时同步
7. **教程页面**：6个完整教程页面，包含详细步骤说明、算法展示、学习路径导航，教程列表页包含学习路径流程图、热门教程卡片、CFOP进阶课程分类
8. **Vite 代理配置**：开发模式和预览模式均配置 `/api` 和 `/media` 代理到后端
9. **公式跳转联动**：首页精选公式点击后通过路由 query 参数传递公式ID，目标页面自动打开详情弹窗
10. **轮播图组件**：支持渐变遮罩层显示标题和描述、悬停暂停、图片加载占位符、点击跳转（支持内部路由和外部链接）、指示器美化等交互效果
11. **图片裁剪组件**：Canvas实现1:1固定比例裁剪框，支持滚轮缩放、防抖拖拽、实时预览、图片压缩
12. **公式编辑器**：支持点击式键盘输入公式记号，分类/难度选择，图片上传或从公式库选择
13. **帖子图片预览**：帖子列表右侧显示1:1比例图片预览，支持多图显示
14. **公式多重筛选**：支持分类、难度、作者三维联合筛选
15. **公式卡片样式优化**：卡片头部展示公式名+难度标签，底部显示"分类名  by 用户名"；公式名、分类名、作者名统一字体样式，提升视觉一致性
16. **401自动清除登录态**：Axios 响应拦截器检测到 401 状态码且本地存在 Token 时，自动清除用户登录状态并提示"登录已失效，请重新登录"，避免过期 Token 残留导致持续报错
17. **错误提示防抖**：相同错误消息 3 秒内只弹一次，配合 Element Plus grouping 合并，避免并发请求失败时刷屏

---

## API 接口文档

启动后端服务后，可通过以下地址访问 API 文档：
- Swagger UI：`http://localhost:8000/api/schema/swagger-ui/`
- Redoc：`http://localhost:8000/api/schema/redoc/`

### 用户系统 API (`/api/`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/users/register/` | POST | 用户注册 |
| `/api/users/login/` | POST | 用户登录（返回 Token） |
| `/api/users/logout/` | POST | 用户退出登录（JWT 黑名单机制） |
| `/api/users/info/` | GET | 获取当前登录用户信息 |
| `/api/users/` | GET | 获取用户列表 |
| `/api/users/{id}/` | GET | 获取指定用户详情 |
| `/api/users/{id}/follow/` | POST | 关注/取消关注用户 |
| `/api/users/{id}/following/` | GET | 获取关注列表 |
| `/api/users/{id}/followers/` | GET | 获取粉丝列表 |
| `/api/profiles/` | GET | 获取用户资料列表 |
| `/api/profiles/{id}/` | GET/PUT/PATCH | 获取/更新用户资料 |

### 论坛系统 API (`/api/forum/`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/forum/posts/` | GET | 获取帖子列表（支持筛选、排序） |
| `/api/forum/posts/` | POST | 创建帖子 |
| `/api/forum/posts/{id}/` | GET | 获取帖子详情（作者信息、标签、图片） |
| `/api/forum/posts/{id}/` | PUT/PATCH/DELETE | 更新/删除帖子 |
| `/api/forum/posts/{id}/like/` | POST | 点赞/取消点赞帖子 |
| `/api/forum/posts/{id}/collect/` | POST | 收藏/取消收藏帖子 |
| `/api/forum/posts/{id}/comments/` | GET | 获取帖子评论列表 |
| `/api/forum/posts/my_posts/` | GET | 获取当前用户的帖子 |
| `/api/forum/posts/collected/` | GET | 获取当前用户收藏的帖子 |
| `/api/forum/posts/hot/` | GET | 获取热门帖子（基于热度排序） |
| `/api/forum/posts/upload_image/` | POST | 上传帖子图片（独立接口） |
| `/api/forum/comments/` | GET/POST | 评论列表/创建评论 |
| `/api/forum/comments/{id}/like/` | POST | 点赞评论 |
| `/api/forum/comments/{id}/dislike/` | POST | 点踩评论 |
| `/api/forum/tags/` | GET | 获取标签列表 |
| `/api/forum/reports/` | POST | 提交举报 |

### 公式库 API (`/api/formula/`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/formula/categories/` | GET | 获取公式分类列表（权限过滤：系统分类+用户自定义） |
| `/api/formula/categories/` | POST | 创建自定义分类 |
| `/api/formula/categories/{id}/` | GET/PUT/DELETE | 分类详情/更新/删除 |
| `/api/formula/categories/my_custom/` | GET | 获取当前用户的自定义分类 |
| `/api/formula/states/` | GET | 获取魔方状态列表 |
| `/api/formula/formulas/` | GET | 获取公式列表（支持筛选/搜索/排序） |
| `/api/formula/formulas/` | POST | 创建公式（管理员/自定义用户） |
| `/api/formula/formulas/{id}/` | GET | 获取公式详情（浏览量+1） |
| `/api/formula/formulas/{id}/` | PUT/PATCH | 更新公式（支持图片压缩裁剪、目标状态绑定、逆公式同步） |
| `/api/formula/formulas/{id}/` | DELETE | 删除公式 |
| `/api/formula/formulas/match/` | POST | 根据当前状态匹配适用公式 |
| `/api/formula/formulas/simple_list/` | GET | 获取简要公式列表（仅 ID 和名称） |
| `/api/formula/formulas/authors/` | GET | 获取公式作者列表（用于筛选） |
| `/api/formula/tags/` | GET | 获取公式标签列表 |
| `/api/formula/collections/` | GET | 获取我的收藏列表 |
| `/api/formula/collections/` | POST | 添加收藏 |
| `/api/formula/collections/{id}/` | DELETE | 取消收藏 |

### 商城系统 API (`/api/shop/`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/shop/categories/` | GET | 获取商品分类列表 |
| `/api/shop/products/` | GET | 获取商品列表（支持筛选） |
| `/api/shop/products/{id}/` | GET | 获取商品详情 |
| `/api/shop/cart/` | GET | 获取购物车列表 |
| `/api/shop/cart/` | POST | 添加商品到购物车 |
| `/api/shop/cart/{id}/` | PUT/PATCH/DELETE | 更新/删除购物车项 |
| `/api/shop/orders/` | GET | 获取订单列表（支持状态筛选） |
| `/api/shop/orders/` | POST | 创建订单（原子扣减库存） |
| `/api/shop/orders/{id}/` | GET | 获取订单详情 |
| `/api/shop/orders/{id}/pay/` | PUT | 获取支付宝支付链接 |
| `/api/shop/orders/{id}/cancel/` | PUT | 取消订单 |
| `/api/shop/orders/{id}/complete/` | PUT | 确认收货 |
| `/api/shop/orders/alipay_notify/` | POST | 支付宝异步回调接口 |
| `/api/shop/addresses/` | GET/POST | 地址列表/创建地址 |
| `/api/shop/addresses/{id}/` | PUT/DELETE | 更新/删除地址 |
| `/api/shop/addresses/{id}/set_default/` | POST | 设置默认地址 |

### 计时器 API (`/api/timer/`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/timer/records/` | GET | 获取计时记录列表 |
| `/api/timer/records/` | POST | 创建计时记录 |
| `/api/timer/records/{id}/` | GET | 获取计时记录详情 |
| `/api/timer/records/{id}/` | DELETE | 删除计时记录 |
| `/api/timer/records/stats/` | GET | 获取分组统计信息 |
| `/api/timer/records/trend/` | GET | 获取按日期分组的趋势统计 |

### 首页 API (`/api/home/`)

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/home/navigation/menus/` | GET | 获取导航菜单列表 |
| `/api/home/navigation/menus/` | POST | 创建导航菜单（管理员） |
| `/api/home/navigation/menus/{id}/` | PUT/DELETE | 更新/删除导航菜单 |
| `/api/home/banners/` | GET | 获取轮播图列表（只返回启用状态） |
| `/api/home/banners/` | POST | 创建轮播图（管理员） |
| `/api/home/banners/{id}/` | PUT/PATCH/DELETE | 更新/删除轮播图 |

---

## 启动方式

### 本地开发启动（Windows）

#### 方式一：一键启停脚本 `dev-local.ps1`（推荐）

项目根目录提供 PowerShell 脚本 `dev-local.ps1`，支持后台一键启动/关闭前后端开发服务器，自动管理进程 PID 和日志。

```powershell
# 启动前后端（后端 127.0.0.1:8000 + 前端 localhost:5173）
powershell -ExecutionPolicy Bypass -File .\dev-local.ps1 start

# 关闭前后端
powershell -ExecutionPolicy Bypass -File .\dev-local.ps1 stop
```

**脚本特性**：
- **后台运行**：前后端均以隐藏窗口后台启动，不占用终端
- **PID 精确管理**：通过 PID + 进程启动时间双重校验，防止误杀被复用的 PID
- **端口检测**：启动前检查端口占用，等待服务就绪（最多 60 秒）
- **失败回滚**：任一服务启动失败时，自动回滚已启动的服务
- **日志分离**：标准输出和错误输出分别保存到 `.dev-local/` 目录（`backend.out.log` / `backend.err.log` / `frontend.out.log` / `frontend.err.log`）
- **依赖校验**：启动前检查 Python 解释器和 npm 是否存在
- **指定 Python 解释器**：固定使用 `E:\software\python\python313\env\cube_api\Scripts\python.exe`
- **不纳入 Git**：通过 `.git/info/exclude` 排除，仅限本地使用

**注意事项**：
- 脚本使用 `--noreload` 启动后端，修改后端代码后需重新执行 `stop` + `start`
- 前端通过 Vite dev server 运行，支持热更新
- `.dev-local/` 目录存放运行时状态和日志，同样不纳入 Git

#### 方式二：手动启动

**后端启动**：
```bash
cd cube_api
python manage.py runserver 8000 --settings=cube_api.settings.dev
```

**前端启动**：
```bash
cd cube_front
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，后端默认运行在 `http://localhost:8000`，Vite 已配置 `/api` 和 `/media` 代理到后端，无需额外处理跨域。

### 服务器部署（Linux + Docker Compose）

#### 一键部署脚本 `deploy.sh`

项目根目录提供 Bash 脚本 `deploy.sh`，封装了从拉取代码到健康检查的完整部署流程。

```bash
# 首次部署或全量更新（构建全部镜像 + 迁移 + 启动所有服务）
bash deploy.sh full

# 仅更新后端（构建 API 镜像 + 迁移 + 重启 API 和 Nginx）
bash deploy.sh api

# 仅更新前端（构建前端镜像 + 重启前端和 Nginx）
bash deploy.sh front
```

> **注意**：`api` 和 `front` 模式要求服务器已执行过 `full` 全量部署，脚本会自动检查所有容器是否存在。

**部署流程（`full` 模式）**：

| 步骤 | 说明 |
|------|------|
| 1. 环境检查 | 校验 Git/Docker/curl 可用、`.env` 存在、Docker Compose 正常、当前用户非 root |
| 2. 拉取代码 | `git pull --ff-only`，输出当前版本 commit |
| 3. 构建镜像 | `docker compose build --pull`（全量）或指定服务 |
| 4. 停止 API | 进入维护窗口，停止 API 容器 |
| 5. 媒体迁移 | 检查旧媒体目录并自动迁移至 `cube_api/media/`（带备份） |
| 6. 等待数据库 | 启动 MySQL 和 Redis，等待 MySQL 健康检查通过（最多 120 秒） |
| 7. 执行迁移 | `docker compose run --rm api python manage.py migrate --noinput` |
| 8. 启动服务 | `docker compose up -d`（全量）或指定服务 |
| 9. 重启 Nginx | 刷新上游容器地址 |
| 10. 健康检查 | HTTP 探测首页和 API 接口（最多 60 秒），验证容器状态和数据库/Redis 连通性 |

**错误处理**：
- 脚本通过 `trap ... ERR` 捕获任何步骤失败，自动输出最近 100 行容器日志和容器状态
- 健康检查 Host 从 `.env` 中的 `ALLOWED_HOSTS` 自动解析
- 禁止使用 `sudo` 运行整个脚本，需使用普通部署用户执行

**常用运维命令**：
```bash
# 查看容器状态
docker compose ps

# 查看后端日志
docker compose logs -f api

# 查看网关日志
docker compose logs -f nginx

# 数据库迁移（手动）
docker compose exec api python manage.py migrate

# 创建超级用户
docker compose exec api python manage.py createsuperuser

# 全部测试（自动切 SQLite 内存库 + Mock Redis + 禁用限流 + MD5）
docker compose exec api python manage.py test
```

#### Docker Compose 服务编排

项目使用 Docker Compose v2 编排五个服务：

| 服务 | 镜像或构建方式 | 说明 |
|------|----------------|------|
| `db` | `mysql:8.0` | MySQL 主数据库，带健康检查和首次初始化脚本 |
| `redis` | `redis:7-alpine` | Redis 缓存、JWT 黑名单和 Session 存储 |
| `api` | `cube_api/Dockerfile` | 多阶段构建 Django 镜像，通过 Gunicorn 提供 API |
| `front` | `cube_front/Dockerfile` | Node 构建 Vue `dist`，运行阶段由 Nginx 提供静态页面 |
| `nginx` | `nginx:1.28-alpine` | 公网网关，转发 API 和前端，直接提供媒体与 Django 静态文件 |

MySQL 使用 `127.0.0.1:3306:3306` 回环映射，远程管理通过 SSH 隧道；API 通过 `condition: service_healthy` 等待 MySQL 健康检查通过后启动。Redis 当前映射 `6379:6379`，生产环境无宿主机直连需求时应移除或限制到回环地址。

生产请求流转：

```text
/api/*    → 网关 Nginx → api:8000
/media/*  → 网关 Nginx → ./cube_api/media
/static/* → 网关 Nginx → collected_static
/*        → 网关 Nginx → front:80 → Vue SPA
```

**持久化与初始化**：

- `mysql_data`、`redis_data` 分别保存 MySQL 和 Redis 数据。
- `collected_static` 在 API 与网关 Nginx 之间共享 Django 静态文件。
- `./cube_api/media` 以宿主机绑定目录同时挂载到 API 和 Nginx，便于纳入 Git 和备份。
- `init_data.sql` 只在 `mysql_data` 为空时自动执行，后续结构更新由 Django migration 处理。
- 前端 `dist` 在 Docker 构建阶段生成并写入前端镜像，不需要在本地生成或提交。
- 禁止执行 `docker compose down -v`，避免删除数据库和 Redis 数据卷。

---

## 数据库配置

后端使用 MySQL 数据库，连接信息通过环境变量配置：
- `DB_NAME`：数据库名（默认 `icube_db`）
- `DB_USER`：用户名（默认 `icube_api`）
- `DB_PASSWORD`：密码（默认 `icube123`）
- `DB_HOST`：主机（默认 `db`）
- `DB_PORT`：端口（默认 `3306`）

同时需要 Redis 服务运行在 `127.0.0.1:6379`（本地）或 `redis:6379`（Docker）。

---

## 总结

ICube 是一个功能完整的魔方学习交流平台，采用现代化技术栈：

- **后端**：Django + DRF + Redis + JWT，提供稳定可靠的 API 服务，支持 Redis 缓存、限流保护、权限控制、浏览量原子更新、图片压缩裁剪与WebP转换
- **前端**：Vue 3 + Element Plus + Three.js，提供丰富的交互体验，包含3D魔方可视化、图片裁剪组件、公式编辑器、响应式导航、状态管理、6个完整教程页面、401自动清除登录态
- **核心功能**：用户管理、论坛社区（含图片预览和全量同步）、公式库（含用户上传、作者筛选、图片处理、浏览量统计和公式跳转）、教程系统（层先法/CFOP/两步OLL/PLL/完整OLL/PLL）、3D魔方可视化（含视角重置动画）、商城购物、支付宝支付、计时器
- **部署方式**：本地开发支持 `dev-local.ps1` 一键启停脚本（Windows PowerShell），生产环境支持 `deploy.sh` 一键部署脚本（Linux Docker Compose）

项目结构清晰，代码组织规范，适合作为学习和交流魔方知识的平台。教程系统覆盖从入门到进阶的完整学习路径，配合公式库的3D动画演示和自定义上传功能，帮助用户更好地学习和掌握魔方技巧。
