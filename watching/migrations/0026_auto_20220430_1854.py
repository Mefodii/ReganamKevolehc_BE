# Generated by Django 3.1.7 on 2022-04-30 15:54

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0025_auto_20220427_2003'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='airing_status',
            field=models.CharField(blank=True, choices=[('Ongoing', 'Ongoing'), ('Completed', 'Completed')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='group',
            name='rating',
            field=models.IntegerField(blank=True, default=0, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
        ),
        migrations.AddField(
            model_name='group',
            name='watched_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='group',
            name='year',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
