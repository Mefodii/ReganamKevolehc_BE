# Generated by Django 3.1.7 on 2022-04-27 17:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0023_auto_20220427_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='video',
            name='status',
            field=models.CharField(choices=[('Dropped', 'Dropped'), ('Planned', 'Planned'), ('Ignored', 'Ignored'), ('Watching', 'Watching'), ('Finished', 'Finished')], max_length=50),
        ),
        migrations.AlterField(
            model_name='video',
            name='year',
            field=models.IntegerField(blank=True, default=1),
        ),
    ]
