## 9. formula 模块

### 9.1 模块职责

魔方公式库：公式分类体系、魔方状态定义、公式 CRUD/匹配/收藏、逆公式自动生成与状态推导。

### 9.2 数据模型（[models.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/models.py)）

| 模型                     | db\_table                      | 核心设计                                                                  |
| ---------------------- | ------------------------------ | --------------------------------------------------------------------- |
| **CubeCategory**       | `formula_cube_category`        | 三维分类：order(阶数)→method(求解方法)→phase(阶段)；系统/自定义（is\_custom, created\_by） |
| **CubeState**          | `formula_cube_state`           | JSON 存储魔方状态（order/blocks/pos/faces）                                   |
| **Formula**            | `formula_formula`              | 核心；thumbnail ImageField、inverse\_notation 自动生成、view\_count 原子递增       |
| **FormulaTag**         | `formula_formula_tag`          | name unique、color                                                     |
| **FormulaTagRelation** | `formula_formula_tag_relation` | 中间表，`unique_together=['formula','tag']`                               |
| **FormulaCollection**  | `formula_formula_collection`   | 收藏，`unique_together=['user','formula']`（幂等）                           |

#### Formula 字段（[L124-L233](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/models.py#L124-L233)）

| 字段                     | 类型              | 说明                                                           |
| ---------------------- | --------------- | ------------------------------------------------------------ |
| category               | FK→CubeCategory | CASCADE                                                      |
| name                   | CharField(200)  | <br />                                                       |
| notation               | TextField       | 公式记号                                                         |
| inverse\_notation      | TextField       | blank（自动生成）                                                  |
| target\_state          | FK→CubeState    | SET\_NULL                                                    |
| pre\_state\_definition | JSONField       | null（前置状态）                                                   |
| thumbnail              | ImageField      | upload\_to='formula\_thumbnails/'（**模型层只有此一个 thumbnail 字段**） |
| difficulty             | IntegerField    | default=1                                                    |
| view\_count            | IntegerField    | default=0（**字段名是 view\_count，不是 views**）                     |
| is\_custom             | BooleanField    | default=False                                                |
| created\_by            | FK→User         | SET\_NULL                                                    |

- `save()`：notation 存在且 inverse\_notation 为空时调用 `FormulaService.generate_inverse_notation`
- `get_pre_state()`：优先 `pre_state_definition`；否则返回 `{derive_from_target, target_state, inverse_notation}` 供推导

### 9.3 URL 路由表（[urls.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/urls.py)）

| 路由                           | 视图                              | 方法             | 权限                                                 | 功能                          |
| ---------------------------- | ------------------------------- | -------------- | -------------------------------------------------- | --------------------------- |
| `/categories/`               | CubeCategoryViewSet             | GET            | AllowAny                                           | 分类列表（未登录仅系统分类）              |
| `/categories/{id}/`          | CubeCategoryViewSet             | GET/PUT/DELETE | IsAuthenticated                                    | 详情/更新/删除（仅创建者）              |
| `/categories/my_custom/`     | CubeCategoryViewSet\@my\_custom | GET            | IsAuthenticated                                    | 我的自定义分类                     |
| `/states/`                   | CubeStateViewSet                | CRUD           | IsAdminOrReadOnly                                  | 魔方状态管理                      |
| `/formulas/`                 | FormulaViewSet                  | GET/POST       | IsAuthenticatedOrReadOnly + IsAdminOrCustomCreator | 公式列表/创建（retrieve 自动 +1 浏览量） |
| `/formulas/{id}/`            | FormulaViewSet                  | GET/PUT/DELETE | 同上                                                 | 详情/更新/删除                    |
| `/formulas/match/`           | FormulaViewSet\@match           | POST           | IsAuthenticated                                    | 按状态匹配公式                     |
| `/formulas/my_custom/`       | FormulaViewSet\@my\_custom      | GET            | IsAuthenticated                                    | 我的自定义公式                     |
| `/formulas/authors/`         | FormulaViewSet\@authors         | GET            | IsAuthenticatedOrReadOnly                          | 公式作者列表（distinct）            |
| `/formulas/simple_list/`     | FormulaViewSet\@simple\_list    | GET            | IsAuthenticatedOrReadOnly                          | 精简列表（帖子编辑器用）                |
| `/tags/`                     | FormulaTagViewSet               | CRUD           | IsAdminOrReadOnly                                  | 标签管理                        |
| `/collections/`              | FormulaCollectionViewSet        | GET/POST       | IsAuthenticated                                    | 收藏列表/添加（get\_or\_create 幂等） |
| `/collections/{formula_id}/` | FormulaCollectionViewSet        | DELETE         | IsAuthenticated                                    | 取消收藏（按公式ID）                 |

### 9.4 视图说明（[views.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/views.py)）

#### FormulaViewSet（[L289-L589](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/views.py#L289-L589)）

- queryset：`Formula.objects.select_related('category','target_state').prefetch_related('tag_relations__tag')`
- permission：`[IsAuthenticatedOrReadOnly, IsAdminOrCustomCreator]`
- **过滤器**：SearchFilter + OrderingFilter + DjangoFilterBackend
  - search\_fields=`['name','notation','description']`
  - ordering\_fields=`['category','difficulty','created_at','view_count']`
  - filterset\_class=`FormulaFilter`
- `get_serializer_class()`：list → FormulaListSerializer；其他 → FormulaSerializer
- **retrieve**：`F('view_count')+1` 原子递增 + `refresh_from_db`
- **自定义 action**：match/my\_custom/authors/simple\_list

### 9.5 序列化器（[serializers.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py)）

#### FormulaSerializer（详情，[L252-L599](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py#L252-L599)）

**thumbnail\_file 与 thumbnail\_path 的区分点**（仅序列化器层）：

- `thumbnail`（只读 SerializerMethodField → `build_image_url`）
- `thumbnail_file`（write\_only FileField，用户上传文件）
- `thumbnail_path`（write\_only CharField，公式库图片引用路径）
- `tag_ids`（write\_only ListField）

**create（[L377-L485](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py#L377-L485)）**：

- 非 staff 已登录用户 → `is_custom=True, created_by=user`
- 缩略图三态处理：
  1. 文件 → `process_image(max_width=512, max_height=512, quality=85, crop_square=True, convert_webp=True)`
  2. 路径 → 剥离 `/media/` 前缀后赋给 `formula.thumbnail.name`
  3. 都无 → `generate_formula_thumbnail(name, notation)` 自动生成
- **target\_state\_id 自动绑定**：category 存在且无 target\_state 时，取该分类下第一个 CubeState
- 标签关联：`FormulaTagRelation.objects.get_or_create`

**update（[L487-L599](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/serializers.py#L487-L599)）**：

- notation 修改时重新生成 inverse\_notation
- **改分类时同步更新 target\_state**：旧 target\_state 不属于新 category 则置空，再绑定新分类下首个状态
- 标签全量同步：先 delete 再 get\_or\_create

### 9.6 服务层（[services.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/services.py)）

#### FormulaService（[L17-L87](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/services.py#L17-L87)）

- `generate_inverse_notation(notation)`：按空格分割 → reversed → `NOTATION_INVERSE_MAP` 取逆 → 拼接
- 覆盖 R/L/U/D/F/B/M/E/S/x/y/z 等正向/逆向/180度三种变体

#### CubeStateService（[L90-L436](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/services.py#L90-L436)）

- `validate_state_definition(state_def)`：多层验证（结构→order→blocks→单块→中心块→相邻块颜色）
- 中心块标准配色 `CENTER_COLORS`：Y/W/B/G/O/R
- 颜色支持 `Y/W/B/G/O/R/-/?`（`-` 不关心，`?` 未知）

#### FormulaMatchService（[L439-L563](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/services.py#L439-L563)）

- `match_formulas(user_state)`：前置状态匹配 + 目标状态匹配
- `_is_state_match`：公式状态中 `-` 跳过，部分匹配
- ⚠️ `_execute_formula` 为占位（转动模拟未实现，退化为原状态比较）

### 9.7 过滤器（[filters.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/filters.py)）

`FormulaFilter`：

- `difficulty = BaseInFilter(lookup_expr='in')` — 支持逗号分隔多值
- `created_by = BaseInFilter(lookup_expr='in')` — 多作者ID
- 示例：`/api/formulas/?difficulty=1,2,3&is_custom=true&created_by=1,2`

### 9.8 权限类（[permissions.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/apps/formula/permissions.py)）

| 权限类                      | 逻辑                                                                                                 |
| ------------------------ | -------------------------------------------------------------------------------------------------- |
| `IsAdminOrReadOnly`      | 读放行；写要求 is\_staff                                                                                  |
| `IsOwnerOrReadOnly`      | 读放行；写检查 created\_by（未使用）                                                                           |
| `IsAdminOrCustomCreator` | has\_permission：SAFE 放行，写需登录；has\_object\_permission：`obj.is_custom and obj.created_by==user` 或管理员 |

### 9.9 management/commands

| 命令                   | 功能                                                |
| -------------------- | ------------------------------------------------- |
| `import_formulas`    | 从 Excel 导入 CFOP 公式（F2L/OLL/PLL），依赖 openpyxl，硬编码路径 |
| `insert_cube_states` | 插入 F2L/OLL/PLL 三个目标状态 + 批量更新公式 target\_state      |

***
