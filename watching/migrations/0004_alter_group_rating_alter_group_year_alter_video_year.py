# Generated by Django 4.0.4 on 2022-08-07 11:35

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0003_alter_group_id_alter_imagemodel_id_alter_video_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='rating',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
        ),
        migrations.AlterField(
            model_name='group',
            name='year',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='video',
            name='year',
            field=models.IntegerField(default=0),
        ),
    ]