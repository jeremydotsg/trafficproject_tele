# Generated by Django 5.0.7 on 2024-07-23 13:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trafficdb', '0014_tgqueueupdate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tgqueueupdate',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='tgqueueupdate',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='tgqueueupdate',
            name='username',
        ),
        migrations.AddField(
            model_name='queuestatus',
            name='queueUserId',
            field=models.BigIntegerField(blank=True, default=None, null=True),
        ),
    ]
