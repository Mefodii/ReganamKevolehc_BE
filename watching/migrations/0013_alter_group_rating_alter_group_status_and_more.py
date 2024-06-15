# Generated by Django 4.2.7 on 2024-05-15 05:17

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0012_rename_links_group_links_arr_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='rating',
            field=models.IntegerField(blank=True, default=0, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
        ),
        migrations.AlterField(
            model_name='group',
            name='status',
            field=models.CharField(blank=True, choices=[('Dropped', 'Dropped'), ('Planned', 'Planned'), ('Ignored', 'Ignored'), ('Premiere', 'Premiere'), ('Watching', 'Watching'), ('Finished', 'Finished')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='group',
            name='year',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='video',
            name='status',
            field=models.CharField(choices=[('Dropped', 'Dropped'), ('Planned', 'Planned'), ('Ignored', 'Ignored'), ('Premiere', 'Premiere'), ('Watching', 'Watching'), ('Finished', 'Finished')], max_length=50),
        ),
    ]
