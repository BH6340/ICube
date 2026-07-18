from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# 💡 核心引入：引入 Django 的静态/媒体目录挂载工具
from django.conf import settings
from django.conf.urls.static import static


api_prefix = 'api'

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. YAML 格式的原始 OpenAPI Schema 文件
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # 2. Swagger UI 交互式文档界面
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # 3. Redoc 文档界面（另一种风格）
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/home/',include('apps.home.urls')),

    path('api/',include('apps.accounts.urls')),

    path('api/forum/', include('apps.forum.urls')),
    path('api/formula/', include('apps.formula.urls')),
    path('api/shop/', include('apps.shop.urls')),
]

# 💡 核心追加：只有在开发阶段（DEBUG = True）时，让 Django 充当文件服务器来映射媒体文件
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)