## 11. home 模块

### 11.1 模块职责

首页导航菜单与轮播图只读查询，支撑前端动态渲染。

### 11.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/home/models.py)）

| 模型                 | 核心设计                                                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| **NavigationMenu** | index unique、label、path、category(choices: main/profile)、sort\_order、match\_paths JSONField(list)。**无父级自关联**——靠 category 字段区分两组导航 |
| **Banner**         | title、description、image ImageField(upload\_to='banners/')、link URLField、sort\_order、is\_active                                   |

> 注：本模块**无层级菜单父级自关联**，与常见设计不同。`match_paths` 用于前端路由高亮匹配。

### 11.3 URL 路由表

| 路由                   | 视图                    | 方法  | 权限       | 功能           |
| -------------------- | --------------------- | --- | -------- | ------------ |
| `/navigation/menus/` | NavigationMenuViewSet | GET | AllowAny | 导航菜单（无分页）    |
| `/banners/`          | BannerViewSet         | GET | AllowAny | 启用中的轮播图（无分页） |

### 11.4 management/commands

`init_menus`：⚠️ **危险操作** `NavigationMenu.objects.all().delete()` 先清空再 `bulk_create`（重置语义，非幂等）。main 6 项 + profile 5 项。

***
