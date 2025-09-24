from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0002_fill_dummy_kyc"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="pancard_number",
            field=models.CharField(
                max_length=10,
                unique=True,
                null=False,
                blank=False,
                help_text="10-character PAN (e.g., ABCDE1234F)",
            ),
        ),
        migrations.AlterField(
            model_name="profile",
            name="aadhaar_number",
            field=models.CharField(
                max_length=12,
                unique=True,
                null=False,
                blank=False,
                help_text="12-digit Aadhaar (e.g., 123456789012)",
            ),
        ),
    ]
