from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_paymenttransaction_delete_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='status',
            field=models.CharField(
                choices=[
                    ("Hold", "Hold"),
                    ("Active", "Active"),
                    ("Deactivated", "Deactivated"),
                    ("Deleted", "Deleted"),
                ],
                default="Hold",
                max_length=20,
            ),
        ),
    ]
