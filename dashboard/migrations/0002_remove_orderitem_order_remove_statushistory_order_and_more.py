# Generated by Django 5.1.6 on 2025-03-10 19:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='order',
        ),
        migrations.RemoveField(
            model_name='statushistory',
            name='order',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='product',
        ),
        migrations.RemoveField(
            model_name='product',
            name='store',
        ),
        migrations.RemoveField(
            model_name='staff',
            name='store',
        ),
        migrations.RemoveField(
            model_name='staff',
            name='user',
        ),
        migrations.RemoveField(
            model_name='statushistory',
            name='changed_by',
        ),
        migrations.RemoveField(
            model_name='store',
            name='owner',
        ),
        migrations.DeleteModel(
            name='Order',
        ),
        migrations.DeleteModel(
            name='OrderItem',
        ),
        migrations.DeleteModel(
            name='Product',
        ),
        migrations.DeleteModel(
            name='Staff',
        ),
        migrations.DeleteModel(
            name='StatusHistory',
        ),
        migrations.DeleteModel(
            name='Store',
        ),
    ]
