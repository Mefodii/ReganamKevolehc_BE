# Generated by Django 4.0.4 on 2022-11-13 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0010_alter_group_airing_status_alter_group_single'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='links',
            field=models.CharField(blank=True, max_length=3000),
        ),
        migrations.AddField(
            model_name='video',
            name='links',
            field=models.CharField(blank=True, max_length=3000),
        ),
    ]