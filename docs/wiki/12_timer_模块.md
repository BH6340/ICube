## 12. timer 模块

### 12.1 模块职责

用户魔方还原计时记录的 CRUD 与统计/趋势分析，以及智能魔方设备管理，**单用户隔离查询**。

### 12.2 数据模型（[models.py](/code/cube_api/cube_api/apps/timer/models.py)）

#### SmartCubeDevice（[L21-L68](/code/cube_api/cube_api/apps/timer/models.py#L21-L68)）

存储用户连接过的智能魔方设备信息，便于下次自动连接。

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| user | FK→User | CASCADE, related_name='smart_cube_devices' |
| mac_address | CharField(20) | MAC 地址 |
| name | CharField(50) | 设备名称，blank |
| last_connected_at | DateTimeField | 最后连接时间，nullable |
| is_active | BooleanField | 是否启用，默认 True |
| created_at | DateTimeField | auto_now_add |

唯一约束：`user + mac_address`（`unique_user_mac`），同一用户同一设备只存一条记录。

#### TimerRecord（[L70-L170](/code/cube_api/cube_api/apps/timer/models.py#L70-L170)）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| user | FK→User | CASCADE, related_name='timer_records' |
| cube_type | CharField(10) | choices: 2x2/3x3/4x4/5x5/other，默认 3x3 |
| method | CharField(20) | choices: layer/cfop/roux/zbll/other，默认 layer |
| timing_mode | CharField(10) | choices: manual/smart，默认 manual |
| time_ms | IntegerField | **毫秒级精度，避免浮点** |
| scramble | TextField | 打乱公式，blank |
| solve_sequence | TextField | 复原步骤序列，nullable |
| observation_time_ms | IntegerField | 观察时间（毫秒），nullable |
| move_count | IntegerField | 复原步数，nullable |
| is_dnf | BooleanField | 是否 DNF，默认 False |
| device | FK→SmartCubeDevice | SET_NULL, nullable，关联设备 |
| created_at | DateTimeField | auto_now_add |

设计要点：
- **向后兼容**：所有智能魔方相关字段均为 nullable，旧数据自动归入 manual 模式
- **设备关联**：`on_delete=SET_NULL`，设备删除后计时记录保留

### 12.3 序列化器（[serializers.py](/code/cube_api/cube_api/apps/timer/serializers.py)）

#### SmartCubeDeviceSerializer（[L13-L35](/code/cube_api/cube_api/apps/timer/serializers.py#L13-L35)）

- fields: id/mac_address/name/last_connected_at/is_active/created_at
- `create` 方法使用 `update_or_create`，同一用户同一 MAC 自动更新而非重复创建

#### TimerRecordSerializer（[L38-L71](/code/cube_api/cube_api/apps/timer/serializers.py#L38-L71)）

- `device_id`：write_only 字段，前端传设备 ID，后端反查 `SmartCubeDevice` 并绑定
- `device`：read_only，嵌套返回设备信息
- `create` 方法自动关联当前用户，校验 `device_id` 属于当前用户

### 12.4 URL 路由表（[urls.py](/code/cube_api/cube_api/apps/timer/urls.py)）

| 路由 | 视图 | 方法 | 权限 | 功能 |
| --- | --- | --- | --- | --- |
| `/records/` | TimerRecordViewSet | GET/POST | IsAuthenticated | 记录列表（分页+过滤）/创建 |
| `/records/{id}/` | TimerRecordViewSet | DELETE | IsAuthenticated | 删除（校验 user 一致） |
| `/records/stats/` | TimerRecordViewSet@stats | GET | IsAuthenticated | 分组统计（best/avg/count/dnf） |
| `/records/trend/` | TimerRecordViewSet@trend | GET | IsAuthenticated | 按日期趋势（默认30天） |
| `/devices/` | SmartCubeDeviceViewSet | GET/POST | IsAuthenticated | 设备列表/注册 |
| `/devices/{id}/` | SmartCubeDeviceViewSet | DELETE | IsAuthenticated | 删除设备（校验 user 一致） |

### 12.5 视图说明（[views.py](/code/cube_api/cube_api/apps/timer/views.py)）

#### SmartCubeDeviceViewSet（[L20-L58](/code/cube_api/cube_api/apps/timer/views.py#L20-L58)）

- 继承 `ModelViewSet`，permission=`[IsAuthenticated]`
- `get_queryset` 过滤当前用户设备，按 `last_connected_at` 倒序
- `list`/`create`/`destroy` 重写返回 `APIResponse`
- `destroy` 校验设备属于当前用户

#### TimerRecordViewSet（[L61-L270](/code/cube_api/cube_api/apps/timer/views.py#L61-L270)）

- 继承 `ModelViewSet`，permission=`[IsAuthenticated]`
- **无 filter_backends**，过滤逻辑全在 `get_queryset` 手动解析
- **get_queryset 单用户隔离**（[L82-L105](/code/cube_api/cube_api/apps/timer/views.py#L82-L105)）：`filter(user=request.user)` + cube_type/method/timing_mode/start_date/end_date
- **list/create/destroy 重写**：返回 `APIResponse`，create 自动关联用户
- **stats action**（[L143-L215](/code/cube_api/cube_api/apps/timer/views.py#L143-L215)）：
  - 按 `cube_type + method + timing_mode` 三维分组
  - 排除 DNF 记录计算 best_time/avg_time
  - 返回 `group_stats`（分组统计）+ `overall_stats`（含 dnf_count/valid_count）
- **trend action**（[L217-L270](/code/cube_api/cube_api/apps/timer/views.py#L217-L270)）：
  - 参数 days（默认30）、cube_type、method、timing_mode
  - 排除 DNF，按 `created_at__date` 分组

### 12.6 Admin 后台（[admin.py](/code/cube_api/cube_api/apps/timer/admin.py)）

基于 django-unfold 定制管理界面。

#### TimerRecordAdmin（[L24-L183](/code/cube_api/cube_api/apps/timer/admin.py#L24-L183)）

- `cube_type_badge`：魔方类型彩色 Badge（2x2青/3x3蓝/4x4绿/5x5橙/other灰）
- `method_badge`：还原方法彩色 Badge（layer绿/cfop紫/roux黄/zbll红/other灰）
- `formatted_time`：毫秒 → `MM:SS.mmm` 可读格式
- `date_hierarchy`、`search_fields`、`list_filter`、`list_select_related`

#### SmartCubeDeviceAdmin（[L186-L215](/code/cube_api/cube_api/apps/timer/admin.py#L186-L215)）

- `is_active_badge`：启用/禁用状态 Badge
- 搜索 user__username / mac_address / name

***
