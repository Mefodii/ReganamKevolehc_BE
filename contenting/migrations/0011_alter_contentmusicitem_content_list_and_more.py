# Generated by Django 4.2.7 on 2024-05-19 17:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('listening', '0005_artist_display_name_release_display_name_and_more'),
        ('contenting', '0010_contentlist_migration_position'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentmusicitem',
            name='content_list',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_music_items', to='contenting.contentlist'),
        ),
        migrations.AlterField(
            model_name='contenttrack',
            name='content_item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracks', to='contenting.contentmusicitem'),
        ),
        migrations.AlterField(
            model_name='contenttrack',
            name='track',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='content_tracks', to='listening.track'),
        ),
    ]
