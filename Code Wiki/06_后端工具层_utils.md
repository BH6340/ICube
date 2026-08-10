## 6. 后端工具层（utils）

### 6.1 common\_response.py — 统一响应（[common\_response.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_response.py)）

| 类                              | 继承             | 用途                       |
| ------------------------------ | -------------- | ------------------------ |
| `APIResponse`                  | DRF `Response` | 通用响应 `{code, msg, data}` |
| `PaginatedResponse`            | APIResponse    | 适配分页器实例                  |
| `PageNumberPaginationResponse` | APIResponse    | 适配 page 对象               |

**状态码约定**：

| code | 含义              | HTTP status |
| ---- | --------------- | ----------- |
| 100  | 请求成功（默认）        | 200         |
| 400  | 请求参数错误          | 200         |
| 403  | 权限不足            | 200         |
| 404  | 资源不存在           | 200         |
| 503  | 服务不可用（如支付宝配置异常） | 200         |
| 998  | 业务逻辑错误          | 跟随 DRF      |
| 999  | 系统内部错误          | 500         |

**响应格式**：

```json
{"code": 100, "msg": "请求成功", "data": {...}}
```

分页响应：

```json
{"code": 100, "msg": "success", "data": {"count": 100, "next": "?page=2", "previous": null, "results": [...]}}
```

前端拦截器将 `code !== 100` 视为错误。

### 6.2 common\_exception.py — 统一异常处理（[common\_exception.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_exception.py)）

核心函数 `common_exception_handler(exc, context)`（[L35](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_exception.py#L35-L127)）：

1. 提取上下文（user email/Anonymous、path、method、view 类名）
2. 调用 DRF 原生 `drf_exception_handler` 获取初步 response
3. **情况 A：DRF 已处理**（业务错误）：
   - `ValidationError` → 取第一个字段第一个错误，格式 `field: error`
   - 其他 dict → 取 detail；list → 取 `[0]`；其他 → str()
   - `logger.warning` + 结构化上下文 → `APIResponse(code=998, msg, status=response.status_code)`
4. **情况 B：未捕获异常**（系统错误）：
   - `logger.error` + 上下文 → `APIResponse(code=999, msg="系统开小差了，请稍后再试", status=500)`
   - 屏蔽敏感堆栈，仅返回友好提示

| 异常类型             | 分支 | code | HTTP status | 日志      |
| ---------------- | -- | ---- | ----------- | ------- |
| ValidationError  | A  | 998  | 400         | warning |
| PermissionDenied | A  | 998  | 403         | warning |
| NotFound         | A  | 998  | 404         | warning |
| APIException 子类  | A  | 998  | 跟随 DRF      | warning |
| 其他 Python 异常     | B  | 999  | 500         | error   |

### 6.3 common\_pagination.py — 统一分页（[common\_pagination.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/common_pagination.py)）

| 类                           | page\_size | max\_page\_size | 用途    |
| --------------------------- | ---------- | --------------- | ----- |
| `UnifiedPagination`         | 20         | 100             | 默认分页器 |
| `LargeResultsSetPagination` | 50         | 500             | 大数据集  |
| `SmallResultsSetPagination` | 10         | 50              | 小数据集  |

重写 `get_paginated_response(data)` 返回 `APIResponse(data={count, next, previous, results})`，与统一响应格式一致。同时提供 `get_paginated_response_schema(schema)` 为 drf-spectacular 生成正确 schema。

### 6.4 image\_url.py — 图片 URL 标准化（[image\_url.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_url.py)）

```python
def build_image_url(relative_path, absolute=False)
```

**处理逻辑**（[L57-L102](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_url.py#L57-L102)）：

1. 空路径 → 返回 `''`
2. `isinstance(relative_path, FieldFile)` → 取 `.name`（**避免触发 .path 属性计算**）
3. 完整 URL（http/https 开头）→ 原样返回
4. 补 `/` 前缀
5. 补 `/media/` 前缀（已存在则跳过）
6. `absolute=True` 时拼接 `settings.SITE_DOMAIN`

**关键约束**（项目规则）：

- **禁止** **`hasattr(relative_path, 'path')`** —— 头像路径以 `/` 开头时会触发 `SuspiciousFileOperation`
- 改用 `isinstance(FieldFile)` 检查后访问 `.name`

**默认返回相对路径**的原因：浏览器 Private Network Access (PNA) 会阻止公网域名直接访问 localhost 图片资源。

### 6.5 image\_processor.py — 图像处理（[image\_processor.py](file:///e:/BH/PyStudy/ICube/cube_api/cube_api/utils/image_processor.py)）

依赖 Pillow。

| 函数                           | 签名                                                                                           | 功能                               |
| ---------------------------- | -------------------------------------------------------------------------------------------- | -------------------------------- |
| `compress_image`             | `(file, max_width=1200, max_height=1200, quality=85, output_format='JPEG')`                  | 缩放压缩；RGBA/LA 转 JPEG 填白；LANCZOS   |
| `convert_to_webp`            | `(file, quality=85)`                                                                         | 转 WebP（有损）                       |
| `crop_to_square`             | `(file)`                                                                                     | 中心裁剪 1:1；透明输出 PNG，否则 JPEG        |
| `process_image`              | `(file, max_width=1200, max_height=1200, quality=85, crop_square=False, convert_webp=False)` | 统一入口                             |
| `generate_formula_thumbnail` | `(formula_name, formula_notation, size=512)`                                                 | 无上传图时自动生成文字缩略图：白底+公式名+记号，输出 WebP |

所有函数返回 `BytesIO`，调用方负责 `seek(0)` 后写入文件存储。

***
