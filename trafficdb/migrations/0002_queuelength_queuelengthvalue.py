# Generated by Django 4.0.6 on 2024-06-03 03:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trafficdb', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='queuelength',
            name='queueLengthValue',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
