## 10. shop 模块

### 10.1 模块职责

魔方商城：商品分类树、购物车、订单全生命周期、支付宝集成、收货地址管理。

### 10.2 数据模型（[models.py](/code/cube_api/cube_api/apps/shop/models.py)）

| 模型                  | db\_table               | 核心设计                                                                                               |
| ------------------- | ----------------------- | -------------------------------------------------------------------------------------------------- |
| **ProductCategory** | `shop_product_category` | parent FK→self(`SET_NULL`)，树形分类                                                                    |
| **Product**         | `shop_product`          | price/original\_price DecimalField、stock Int、images JSONField、thumbnail ImageField、specs JSONField |
| **Cart**            | `shop_cart`             | user+product 双 FK                                                                                  |
| **Order**           | `shop_order`            | order\_no unique、total\_amount Decimal(12,2)、status 状态机、address JSONField（快照）                      |
| **OrderItem**       | `shop_order_item`       | **price 下单时快照**、quantity、selected\_spec                                                            |
| **Address**         | `shop_address`          | is\_default 唯一性、`full_address` property                                                            |

**订单状态机**（[L156](/code/cube_api/cube_api/apps/shop/models.py#L156-L162)）：

```
pending（待付款）→ paid（已付款）→ shipped（已发货）→ completed（已完成）
                  ↘ cancelled（已取消）
        paid → cancelled
```

**关键设计**：

- 订单号 `Order.generate_order_no()`：`ORD` + 时间戳(14) + UUID 前 8 位大写
- **库存并发控制**：`F` 表达式原子扣减
- **价格快照**：OrderItem.price 记录下单时价格
- 无软删除，物理删除 + 事务保证

### 10.3 URL 路由表（[urls.py](/code/cube_api/cube_api/apps/shop/urls.py)）

| 路由                             | 视图                           | 方法                  | 权限              | 功能                                |
| ------------------------------ | ---------------------------- | ------------------- | --------------- | --------------------------------- |
| `/categories/`                 | ProductCategoryViewSet       | GET                 | AllowAny        | 分类树                               |
| `/products/`                   | ProductViewSet               | GET                 | AllowAny        | 商品列表（category/price/keyword/sort） |
| `/cart/`                       | CartViewSet                  | GET/POST/PUT/DELETE | IsAuthenticated | 购物车                               |
| `/orders/`                     | OrderViewSet                 | GET/POST            | IsAuthenticated | 订单 CRUD                           |
| `/orders/{id}/pay/`            | OrderViewSet\@pay            | PUT                 | IsAuthenticated | 获取支付宝支付链接                         |
| `/orders/{id}/cancel/`         | OrderViewSet\@cancel         | PUT                 | IsAuthenticated | 取消（库存回滚）                          |
| `/orders/{id}/complete/`       | OrderViewSet\@complete       | PUT                 | IsAuthenticated | 确认收货                              |
| `/orders/notify/`              | OrderViewSet\@alipay\_notify | POST                | **AllowAny**    | 支付宝异步回调                           |
| `/addresses/`                  | AddressViewSet               | GET/POST/PUT/DELETE | IsAuthenticated | 地址 CRUD                           |
| `/addresses/{id}/set_default/` | AddressViewSet\@set\_default | POST                | IsAuthenticated | 设默认                               |

### 10.4 视图说明（[views.py](/code/cube_api/cube_api/apps/shop/views.py)）

#### OrderViewSet（[L192-L426](/code/cube_api/cube_api/apps/shop/views.py#L192-L426)）

- `get_queryset`：过滤当前用户 + status 筛选
- `retrieve`：支持 order\_no 或 id 双查询
- **create** **`@transaction.atomic`**（[L240-L307](/code/cube_api/cube_api/apps/shop/views.py#L240-L307)）：F 表达式扣库存/加销量、删购物车、生成订单与明细
- `pay` action：调 `generate_alipay_url`，失败 `code=503`
- `alipay_notify` action（[L377-L426](/code/cube_api/cube_api/apps/shop/views.py#L377-L426)）：
  - `permission_classes=[AllowAny]`
  - 先读 `request.body` 再读 `request.data`
  - `verify_alipay_notify` **双重验签**
  - `select_for_update` 锁定订单（幂等）
  - 仅 pending→paid
  - 返回纯文本 `'success'`/`'fail'`

#### CartViewSet（[L112-L189](/code/cube_api/cube_api/apps/shop/views.py#L112-L189)）

- `get_queryset` 过滤当前用户
- create：相同商品+相同规格用 `F('quantity')+quantity` 合并
- update：quantity≤0 自动删除；>stock 返回 `code=400`

#### AddressViewSet（[L429-L530](/code/cube_api/cube_api/apps/shop/views.py#L429-L530)）

- create/update 保证同用户仅一个默认地址
- destroy 删默认地址时自动将首地址设为默认

### 10.5 支付宝集成（[alipay\_config.py](/code/cube_api/cube_api/apps/shop/alipay_config.py)）

基于 `python-alipay-sdk`。

| 函数/配置                                                  | 位置                                                                                              | 关键点                                                                                                                           |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `ALIPAY_CONFIG`                                        | [L25-L38](/code/cube_api/cube_api/apps/shop/alipay_config.py#L25-L38)     | app\_id、私钥/公钥路径 `os.path.join(BASE_DIR,'keys',...)`、notify\_url=`http://{SERVER_HOST}/api/shop/orders/notify/`、debug=True（沙箱） |
| `get_alipay_client()`                                  | [L153-L206](/code/cube_api/cube_api/apps/shop/alipay_config.py#L153-L206) | 文件存在性检查；sign\_type=`RSA2`；启动打印公钥 modulus 指纹                                                                                   |
| `generate_alipay_url(order_no, total_amount, subject)` | [L209-L250](/code/cube_api/cube_api/apps/shop/alipay_config.py#L209-L250) | `total_amount=str(total_amount)` 强制两位小数字符串；沙箱/生产网关切换                                                                          |
| `verify_alipay_notify(data, raw_body)`                 | [L295-L355](/code/cube_api/cube_api/apps/shop/alipay_config.py#L295-L355) | **双重验签**：SDK verify + 失败时手动 RSA2 验签；验签 message/sign 落盘便于核对                                                                    |

**密钥路径**：`apps/shop/keys/app_private_key.pem` + `alipay_public_key.pem`，已 `.gitignore`，**禁止提交版本控制**。

### 10.6 management/commands

`init_shop_data`：初始化商品分类（6 个顶级）与 12 个示例商品，`get_or_create` 幂等。

***
