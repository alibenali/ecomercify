# Generated manually for staff permissions

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0002_alter_staff_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='permissions',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
