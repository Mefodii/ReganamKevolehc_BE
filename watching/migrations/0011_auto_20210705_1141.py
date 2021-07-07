# Generated by Django 3.1.7 on 2021-07-05 08:41

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0010_auto_20210417_1621'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('alias', models.CharField(blank=True, max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('check_date', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='video',
            name='check_date',
        ),
        migrations.AddField(
            model_name='video',
            name='episodes',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='video',
            name='rating',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(10)]),
        ),
        migrations.AlterField(
            model_name='video',
            name='alias',
            field=models.CharField(blank=True, max_length=1000),
        ),
        migrations.AlterField(
            model_name='video',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='video',
            name='parent_video',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='watching.video'),
        ),
        migrations.AlterField(
            model_name='video',
            name='status',
            field=models.CharField(choices=[('Dropped', 'Dropped'), ('Planned', 'Planned'), ('Ignored', 'Ignored'), ('Watching', 'Watching'), ('Finished', 'Finished')], default='Finished', max_length=50),
        ),
        migrations.DeleteModel(
            name='Season',
        ),
        migrations.AddField(
            model_name='video',
            name='video_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='videos', to='watching.videogroup'),
        ),
    ]