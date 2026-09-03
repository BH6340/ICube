# -*- coding: utf-8 -*-
"""
支付宝配置与支付集成模块

该模块负责处理支付宝支付的核心逻辑，包括：
    - 支付宝客户端初始化
    - 支付链接生成（网页支付）
    - 二维码生成（扫码支付）
    - 异步回调签名验证

设计特点：
    - **双重验签机制**：SDK 验签 + 手动 RSA2 验签，确保支付安全
    - **沙箱/生产环境隔离**：通过 debug 参数自动切换网关
    - **密钥文件动态加载**：支持路径配置和文件存在性检查
    - **公钥指纹校验**：启动时打印公钥指纹，便于与支付宝后台对比
"""

from alipay import AliPay
import os

from loguru import logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_DEBUG = os.getenv('ALIPAY_DEBUG', 'True').lower() == 'true'
_SCHEME = os.getenv('ALIPAY_SCHEME') or ('http' if _DEBUG else 'https')
_SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')

ALIPAY_CONFIG = {
    # 应用 ID：支付宝开放平台创建的应用唯一标识
    'app_id': os.getenv('ALIPAY_APP_ID', '9021000162660623'),
    # 应用私钥路径：用于对请求进行签名，必须妥善保管，不可泄露
    'app_private_key_path': os.path.join(BASE_DIR, 'keys', 'app_private_key.pem'),
    # 支付宝公钥路径：用于验证支付宝返回数据的签名，由支付宝生成
    'alipay_public_key_path': os.path.join(BASE_DIR, 'keys', 'alipay_public_key.pem'),
    # 异步回调地址：支付宝支付成功后主动通知的接口，必须是公网可访问的 POST 接口
    'notify_url': f"{_SCHEME}://{_SERVER_HOST}/api/shop/orders/notify/",
    # 同步回调地址前缀：用户支付完成后跳转的页面地址
    'return_url_prefix': f"{_SCHEME}://{_SERVER_HOST}/shop/pay",
    # 调试模式：True 表示使用沙箱环境，生产环境通过 ALIPAY_DEBUG=False 切换
    'debug': _DEBUG,
}

"""
===========================================
  支付宝沙箱配置详细指南
===========================================

【第一步】注册支付宝开放平台账号
1. 访问: https://open.alipay.com/platform/home.htm
2. 使用支付宝扫码登录

【第二步】进入沙箱环境
1. 登录后，在控制台首页找到"沙箱"入口
2. 点击进入沙箱应用管理

【第三步】获取 APP_ID
1. 在沙箱应用详情页，找到"应用ID"
2. 将其填入上方 'app_id' 字段

【第四步】生成密钥（关键！）
1. 使用支付宝官方密钥工具生成：
   - Windows工具下载: https://opendocs.alipay.com/open/291/106097
   - 在线生成: https://miniu.alipay.com/keytool/create

2. 生成参数：
   - 密钥格式：PKCS8
   - 密钥长度：2048
   - 签名算法：RSA2（推荐）

3. 生成后会得到：
   - 应用私钥（APP PRIVATE KEY）：由开发者保管，用于签名请求
   - 应用公钥（APP PUBLIC KEY）：上传到支付宝后台

4. 将应用私钥粘贴到文件：
   keys/app_private_key.pem

5. 将应用公钥上传到支付宝沙箱：
   - 在沙箱应用的"接口加签方式"中设置
   - 选择"RSA2(SHA256)密钥"
   - 粘贴应用公钥并保存

【第五步】获取支付宝公钥
1. 在沙箱应用的"接口加签方式"中
2. 保存应用公钥后，会自动生成"支付宝公钥"
3. 将支付宝公钥粘贴到文件：
   keys/alipay_public_key.pem

   ⚠️ 注意：是"支付宝公钥"，不是"应用公钥"！

【第六步】配置回调地址
1. notify_url（异步回调）：
   - 格式: http://你的公网地址/api/shop/orders/notify/
   - 必须是公网可访问的 POST 接口
   - 用于支付宝通知支付结果，可靠性更高

2. return_url（同步回调）：
   - 格式: http://你的公网地址/shop/pay/callback
   - 用户支付完成后跳转的页面，可能被用户拦截

【第七步】本地开发公网访问（重要！）
支付宝回调需要公网地址，本地开发需要使用内网穿透工具：

方法1：使用 ngrok（推荐）
1. 下载 ngrok: https://ngrok.com/download
2. 注册账号并获取 token
3. 运行命令: ngrok http 8000
4. 获取公网地址（如: https://abc123.ngrok.io）

方法2：使用花生壳
1. 下载花生壳: https://hsk.oray.com/
2. 注册账号并创建映射
3. 将本地8000端口映射到公网

方法3：使用阿里云内网穿透
1. 下载工具: https://help.aliyun.com/document_detail/64672.html
2. 配置映射规则

【第八步】测试支付
1. 使用沙箱买家账号：
   - 在沙箱环境中查看"沙箱账户"
   - 获取买家账号和密码

2. 在支付宝APP中登录沙箱买家账号
3. 扫码支付测试

【常见问题排查】

❌ 支付失败，提示签名错误
- 检查应用私钥是否正确（格式、内容）
- 检查支付宝公钥是否正确（是支付宝公钥，不是应用公钥）
- 确保密钥格式为 PKCS8
- 检查是否使用了正确的签名算法（RSA2）

❌ 支付成功但订单状态未更新
- 检查 notify_url 是否公网可访问
- 检查防火墙是否允许外部访问
- 检查回调接口是否正确处理 POST 请求
- 使用 ngrok 日志查看回调请求

❌ 支付宝沙箱API返回500错误
- 检查 APP_ID 是否正确
- 检查密钥是否正确配置
- 检查请求参数是否完整
- 在代码中添加详细日志排查

【注意事项】
1. debug=True 表示使用沙箱环境，上线前改为 False
2. 密钥文件不要提交到版本控制系统（已加入 .gitignore）
3. 回调地址必须是 http/https，不能是 localhost
4. 支付金额必须大于0

===========================================
"""


def get_alipay_client():
    """
    获取支付宝客户端实例

    初始化 AliPay SDK 客户端，处理密钥加载和配置验证。

    返回值：
        AliPay | None: 配置成功返回客户端实例，否则返回 None

    设计要点：
        - **密钥文件动态加载**：支持路径配置和文件存在性检查
        - **公钥指纹校验**：启动时打印公钥模数前60位，便于与支付宝后台对比
        - **使用 RSA2 算法**：安全性更高，是支付宝推荐的标准算法
    """
    app_id = ALIPAY_CONFIG['app_id']
    app_private_key_path = ALIPAY_CONFIG['app_private_key_path']
    alipay_public_key_path = ALIPAY_CONFIG['alipay_public_key_path']

    if not app_id:
        return None

    app_private_key = ''
    if app_private_key_path and os.path.exists(app_private_key_path):
        with open(app_private_key_path, 'r') as f:
            app_private_key = f.read()

    alipay_public_key = ''
    if alipay_public_key_path and os.path.exists(alipay_public_key_path):
        with open(alipay_public_key_path, 'r') as f:
            alipay_public_key = f.read()

    if not app_private_key or not alipay_public_key:
        logger.warning(f"密钥文件缺失: private={bool(app_private_key)}, alipay_public={bool(alipay_public_key)}")
        return None

    # 启动时打印公钥指纹，方便与支付宝后台对比
    try:
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
        pub = load_pem_public_key(alipay_public_key.encode())
        nums = pub.public_numbers()
        logger.info(f"已加载支付宝公钥, modulus 前60位: {str(nums.n)[:60]}")
    except Exception:
        pass

    alipay = AliPay(
        appid=app_id,
        app_notify_url=ALIPAY_CONFIG['notify_url'],
        app_private_key_string=app_private_key,
        alipay_public_key_string=alipay_public_key,
        sign_type='RSA2',
        debug=ALIPAY_CONFIG['debug'],
    )

    return alipay


def generate_alipay_url(order_no, total_amount, subject, return_url=None):
    """
    生成支付宝网页支付 URL

    Args:
        order_no: 订单号（唯一标识）
        total_amount: 支付金额（Decimal 或 float）
        subject: 订单标题（显示在支付页面）
        return_url: 支付完成后跳转地址（可选，默认为配置的前缀 + 订单号）

    返回值：
        str | None: 支付 URL 或 None（配置失败时）

    设计要点：
        - **沙箱/生产环境自动切换**：根据 debug 参数选择不同网关
        - **URL 兼容性处理**：python-alipay-sdk 3.x 版本返回格式不一致，统一处理
    """
    alipay = get_alipay_client()
    if not alipay:
        return None

    if ALIPAY_CONFIG['debug']:
        gateway = 'https://openapi-sandbox.dl.alipaydev.com/gateway.do'
    else:
        gateway = 'https://openapi.alipay.com/gateway.do'

    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order_no,
        total_amount=str(total_amount),
        subject=subject,
        return_url=return_url or f"{ALIPAY_CONFIG['return_url_prefix']}/{order_no}",
        notify_url=ALIPAY_CONFIG['notify_url'],
    )

    # python-alipay-sdk 3.x 某些版本返回完整 URL，某些版本只返回参数字符串，统一处理
    if order_string.startswith('http'):
        pay_url = order_string
    else:
        pay_url = f'{gateway}?{order_string}'

    logger.info(f"生成支付宝支付链接 - 订单 {order_no}\n  gateway: {gateway}\n  notify_url: {ALIPAY_CONFIG['notify_url']}\n  full_url: {pay_url}")
    return pay_url


def generate_alipay_qr_code(order_no, total_amount, subject):
    """
    生成支付宝扫码支付二维码

    Args:
        order_no: 订单号（唯一标识）
        total_amount: 支付金额（Decimal 或 float）
        subject: 订单标题

    返回值：
        str | None: 二维码内容（URL）或 None（配置失败时）

    设计要点：
        - **使用预下单接口**：api_alipay_trade_precreate 返回二维码内容
        - **异常详细记录**：捕获异常时记录完整信息，便于排查问题
    """
    alipay = get_alipay_client()
    if not alipay:
        logger.warning(f"QR码生成失败 - 订单 {order_no}: get_alipay_client() 返回 None (检查密钥文件)")
        return None

    try:
        result = alipay.api_alipay_trade_precreate(
            out_trade_no=order_no,
            total_amount=str(total_amount),
            subject=subject,
            notify_url=ALIPAY_CONFIG['notify_url'],
        )

        if result.get('code') == '10000':
            qr_code = result.get('qr_code')
            logger.info(f"QR码生成成功 - 订单 {order_no}")
            return qr_code
        else:
            logger.error(f"QR码生成失败 - 订单 {order_no}: 支付宝返回 {result}")
            return None
    except Exception as e:
        logger.error(f"QR码生成异常 - 订单 {order_no}: type={type(e).__name__}, msg={e}, args={e.args}")
        logger.error(f"  异常详情: dir={[a for a in dir(e) if not a.startswith('_')]}")
        return None


def verify_alipay_notify(data, raw_body=None):
    alipay = get_alipay_client()
    if not alipay:
        return False

    data_dict = {k: v[0] if isinstance(v, list) else v for k, v in data.items()}
    sign_b64 = data_dict.pop('sign', '')
    if not sign_b64:
        return False

    # 方法一：SDK verify
    test_dict = dict(data_dict)
    sdk_ok = alipay.verify(test_dict, sign_b64)
    logger.info(f"SDK 验签结果: {sdk_ok}")
    if sdk_ok:
        return True

    # 方法二：用原始 POST body 精确验签
    try:
        import base64
        from urllib.parse import unquote, urlencode
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        key_path = ALIPAY_CONFIG['alipay_public_key_path']
        if not os.path.exists(key_path):
            logger.error(f"支付宝公钥文件不存在: {key_path}")
            return False

        with open(key_path, 'r') as f:
            pub_key = load_pem_public_key(f.read().encode())

        if raw_body:
            body_str = raw_body.decode('utf-8') if isinstance(raw_body, bytes) else raw_body
            pairs = body_str.split('&')
            msg_pairs = [
                (p.split('=', 1)[0], unquote(p.split('=', 1)[1]))
                for p in pairs if '=' in p and not p.startswith(('sign=', 'sign_type='))
            ]
            msg_pairs.sort(key=lambda x: x[0])
            message = '&'.join(f'{k}={v}' for k, v in msg_pairs)
        else:
            verify_data = {k: v for k, v in data_dict.items() if k not in ('sign', 'sign_type')}
            message = urlencode(sorted(verify_data.items()), doseq=False)

        signature_bytes = base64.b64decode(sign_b64)
        pub_key.verify(signature_bytes, message.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
        logger.info("手动 RSA2 验签通过")
        return True
    except Exception as e:
        logger.error(f"手动 RSA2 验签异常: {type(e).__name__}: {e}")
        return False