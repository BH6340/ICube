from django.db import migrations


def add_user_navigation(apps, schema_editor):
    NavigationMenu = apps.get_model('home', 'NavigationMenu')
    NavigationMenu.objects.update_or_create(
        index='7',
        defaults={
            'label': '魔友',
            'path': '/users',
            'category': 'main',
            'sort_order': 55,
            'match_paths': ['/users'],
        },
    )


def remove_user_navigation(apps, schema_editor):
    NavigationMenu = apps.get_model('home', 'NavigationMenu')
    NavigationMenu.objects.filter(index='7').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_banner'),
    ]

    operations = [
        migrations.RunPython(
            add_user_navigation,
            remove_user_navigation,
        ),
    ]
