# Generated by Django 4.0.4 on 2022-06-01 06:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='comment',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='video',
            name='current_episode',
            field=models.IntegerField(default=0),
        ),
    ]
