from django.db import migrations


def set_users_active(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.all().update(is_active=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_employee_id_and_photo'),
    ]

    operations = [
        migrations.RunPython(set_users_active, reverse_code=noop),
    ]

