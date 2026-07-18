from rest_framework import serializers
from .models import NavigationMenu

class NavigationMenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavigationMenu
        fields = ('index', 'label', 'path', 'category', 'match_paths')