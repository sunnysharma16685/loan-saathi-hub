from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_nullable_pan_aadhaar'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE main_profile
                ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'pending';
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
