# Generated by Django 4.2.7 on 2024-05-20 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listening', '0005_artist_display_name_release_display_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='track',
            name='is_clean',
            field=models.BooleanField(default=False),
        ),
    ]