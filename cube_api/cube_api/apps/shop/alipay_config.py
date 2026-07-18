from alipay import AliPay
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ALIPAY_CONFIG = {
    'app_id': '9021000162660623',
    'app_private_key_path': os.path.join(BASE_DIR, 'keys', 'app_private_key.pem'),
    'alipay_public_key_path': os.path.join(BASE_DIR, 'keys', 'alipay_public_key.pem'),
    'notify_url': 'http://121.4.62.163/api/shop/orders/notify/',
    'return_url': 'http://121.4.62.163/shop/pay/callback',
    'debug': True,
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
   - 应用私钥（APP PRIVATE KEY）
   - 应用公钥（APP PUBLIC KEY）

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
   - 用于支付宝通知支付结果

2. return_url（同步回调）：
   - 格式: http://你的公网地址/shop/pay/callback
   - 用户支付完成后跳转的页面

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
        return None

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
        return_url=return_url or ALIPAY_CONFIG['return_url'],
        notify_url=ALIPAY_CONFIG['notify_url'],
    )

    return f'{gateway}?{order_string}'


def generate_alipay_qr_code(order_no, total_amount, subject):
    alipay = get_alipay_client()
    if not alipay:
        return None

    result = alipay.api_alipay_trade_precreate(
        out_trade_no=order_no,
        total_amount=str(total_amount),
        subject=subject,
        notify_url=ALIPAY_CONFIG['notify_url'],
    )

    if result.get('code') == '10000':
        return result.get('qr_code')
    return None


def verify_alipay_notify(data):
    alipay = get_alipay_client()
    if not alipay:
        return False

    return alipay.verify(data)