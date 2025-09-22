from django.db import migrations
from django.utils import timezone

def force_mark_0002(apps, schema_editor):
    from django.db import connection

    with connection.cursor() as cursor:
        # Insert only if not exists
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
        migrations.RunPython(force_mark_0002, migrations.RunPython.noop),
    ]
