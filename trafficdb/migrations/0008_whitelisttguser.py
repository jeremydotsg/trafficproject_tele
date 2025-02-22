# Generated by Django 4.2.13 on 2024-07-02 03:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trafficdb', '0007_alter_blockedtguser_start_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='WhitelistTgUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_id', models.BigIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('start_at', models.DateTimeField(auto_now_add=True)),
                ('end_at', models.DateTimeField(blank=True, null=True)),
                ('remarks', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
    ]
