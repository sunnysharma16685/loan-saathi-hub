from django.db import migrations
from django.utils import timezone

def mark_as_applied(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO django_migrations (app, name, applied)
            SELECT 'main', '0002_add_status_field', %s
            WHERE NOT EXISTS (
                SELECT 1 FROM django_migrations
                WHERE app='main' AND name='0002_add_status_field'
            )
        """, [timezone.now()])

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_nullable_pan_aadhaar'),
    ]

    operations = [
        migrations.RunPython(mark_as_applied, migrations.RunPython.noop),
    ]
