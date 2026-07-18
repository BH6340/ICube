from django.apps import AppConfig


class ForumConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.forum'
    label = 'forum'
    verbose_name = '论坛'
