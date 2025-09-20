from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),  # depends on your initial migration
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ("Hold", "Hold"),
                    ("Active", "Active"),
                    ("Deactivated", "Deactivated"),
                    ("Deleted", "Deleted"),
                ],
                default="Hold",
            ),
        ),
    ]
