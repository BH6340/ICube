from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import NavigationMenu
from .serializers import NavigationMenuSerializer
from utils.common_response import APIResponse  # 保持你项目的统一返回格式


class NavigationMenuViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NavigationMenu.objects.all()
    serializer_class = NavigationMenuSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(code=100, msg="获取成功", data=serializer.data)
