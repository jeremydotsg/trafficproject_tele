# Generated by Django 4.2.13 on 2024-06-09 01:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trafficdb', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='queuestatus',
            name='queueIP',
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
    ]
