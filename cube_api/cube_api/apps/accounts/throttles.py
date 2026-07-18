# throttles.py
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.viewsets import GenericViewSet


class LoginRateThrottle(SimpleRateThrottle):
    """
    针对登录接口的自定义限流，结合了 IP 和尝试登录的 Email
    """
    scope = 'login_scope'  # 对应 settings.py 中的 'login_scope'

    def get_cache_key(self, request, view: GenericViewSet):
        # 仅对登录动作生效
        if view.action != 'login':
            return None

        # 获取用户尝试登录的 email
        user_data = request.data.get('user', {})
        email = user_data.get('email', '')

        if not email:
            return None  # 如果没传 email，交由其他校验处理

        # 获取请求的真实 IP
        ident = self.get_ident(request)

        # 生成 Redis 中独一无二的 Key
        # 比如：throttle_login_scope_192.168.1.1_test@example.com
        return self.cache_format % {
            'scope': self.scope,
            'ident': f"{ident}_{email}"
        }