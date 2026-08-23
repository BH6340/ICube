## 12. timer 模块

### 12.1 模块职责

用户魔方还原计时记录的 CRUD 与统计/趋势分析，**单用户隔离查询**。

### 12.2 数据模型（[models.py](/code/cube_api/cube_api/apps/timer/models.py)）

#### TimerRecord（[L20-L91](/code/cube_api/cube_api/apps/timer/models.py#L20-L91)）

| 字段          | 类型            | 约束                                      |
| ----------- | ------------- | --------------------------------------- |
| user        | FK→User       | CASCADE, related\_name='timer\_records' |
| cube\_type  | CharField(10) | choices: 2x2/3x3/4x4/5x5/other          |
| method      | CharField(20) | choices: layer/cfop/roux/zbll/other     |
| time\_ms    | IntegerField  | **毫秒级精度，避免浮点**                          |
| scramble    | TextField     | blank，打乱公式                              |
| created\_at | DateTimeField | auto\_now\_add                          |

### 12.3 URL 路由表

| 路由                | 视图                        | 方法         | 权限              | 功能                   |
| ----------------- | ------------------------- | ---------- | --------------- | -------------------- |
| `/records/`       | TimerRecordViewSet        | GET/POST   | IsAuthenticated | 记录列表/创建              |
| `/records/{id}/`  | TimerRecordViewSet        | GET/DELETE | IsAuthenticated | 详情/删除（校验 user 一致）    |
| `/records/stats/` | TimerRecordViewSet\@stats | GET        | IsAuthenticated | 分组统计（best/avg/count） |
| `/records/trend/` | TimerRecordViewSet\@trend | GET        | IsAuthenticated | 按日期趋势（默认30天）         |

### 12.4 视图说明（[views.py](/code/cube_api/cube_api/apps/timer/views.py)）

#### TimerRecordViewSet（[L29-L200](/code/cube_api/cube_api/apps/timer/views.py#L29-L200)）

- 继承 `ModelViewSet`，permission=`[IsAuthenticated]`
- **无 filter\_backends**，过滤逻辑全在 `get_queryset` 与 action 内手动解析
- **get\_queryset 单用户隔离**（[L49-L75](/code/cube_api/cube_api/apps/timer/views.py#L49-L75)）：`filter(user=request.user)` + cube\_type/method/start\_date/end\_date
- **stats action**（[L105-L155](/code/cube_api/cube_api/apps/timer/views.py#L105-L155)）：`values('cube_type','method').annotate(total_count=Count('id'), best_time=Min('time_ms'), avg_time=Avg('time_ms'))`
- **trend action**（[L157-L200](/code/cube_api/cube_api/apps/timer/views.py#L157-L200)）：参数 days（默认30），按 `created_at__date` 分组

***
