from django.apps import AppConfig


class TimerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.timer'
    label = 'timer'
    verbose_name = '计时器'