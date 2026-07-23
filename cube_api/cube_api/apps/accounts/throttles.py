# -*- coding: utf-8 -*-
"""
自定义限流类

该模块定义了针对登录接口的自定义限流类，防止暴力破解攻击。

核心限流类：
    - LoginRateThrottle: 针对登录接口的限流，结合 IP 和邮箱

设计原理：
    - 使用 IP + 邮箱的组合作为限流键，防止同一 IP 使用不同邮箱暴力破解
    - 配合 settings.py 中的 'login_scope' 配置限流频率
    - 继承 DRF 的 SimpleRateThrottle，自动使用 Redis 存储限流计数
"""
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.viewsets import GenericViewSet


class LoginRateThrottle(SimpleRateThrottle):
    """
    登录接口自定义限流类

    针对登录接口的限流，结合 IP 地址和尝试登录的邮箱，防止暴力破解攻击。

    限流键格式：
        throttle_login_scope_{IP}_{email}

    配置方式：
        在 settings.py 中配置：
        REST_FRAMEWORK = {
            'DEFAULT_THROTTLE_RATES': {
                'login_scope': '5/minute',  # 每分钟最多 5 次尝试
            }
        }
    """
    # 限流范围名称，对应 settings.py 中的 'login_scope'
    scope = 'login_scope'

    def get_cache_key(self, request, view: GenericViewSet):
        """
        生成限流缓存键

        仅对登录动作生效，使用 IP + 邮箱的组合作为限流键。

        Args:
            request: HTTP 请求对象
            view: 视图对象

        Returns:
            限流缓存键（字符串）或 None（不限流）
        """
        # 仅对登录动作生效，其他动作不限流
        if view.action != 'login':
            return None

        # 获取用户尝试登录的邮箱（支持嵌套的 user 键）
        user_data = request.data.get('user', {})
        email = user_data.get('email', '')

        # 如果没有传邮箱，交由其他校验处理（不限流）
        if not email:
            return None

        # 获取请求的真实 IP 地址
        # get_ident 方法会自动处理代理头（如 X-Forwarded-For）
        ident = self.get_ident(request)

        # 生成 Redis 中独一无二的限流键
        # 格式：throttle_login_scope_{IP}_{email}
        # 例如：throttle_login_scope_192.168.1.1_test@example.com
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"{ident}_{email}"
        }