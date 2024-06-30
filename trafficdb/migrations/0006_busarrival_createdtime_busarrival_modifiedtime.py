# Generated by Django 4.2.13 on 2024-06-15 09:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('trafficdb', '0005_busarrival'),
    ]

    operations = [
        migrations.AddField(
            model_name='busarrival',
            name='createdTime',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='busarrival',
            name='modifiedTime',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
