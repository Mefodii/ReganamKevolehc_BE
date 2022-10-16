# Generated by Django 4.0.4 on 2022-09-21 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenting', '0003_alter_contentwatcher_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contentitem',
            name='download_status',
            field=models.CharField(choices=[('NONE', 'NONE'), ('DOWNLOADING', 'DOWNLOADING'), ('DOWNLOADED', 'DOWNLOADED'), ('UNABLE', 'UNABLE'), ('MISSING', 'MISSING')], max_length=50),
        ),
        migrations.AlterField(
            model_name='contentitempart',
            name='status',
            field=models.CharField(choices=[('NONE', 'NONE'), ('CHECKED', 'CHECKED'), ('ADD', 'ADD'), ('SKIP', 'SKIP'), ('DUPLICATE', 'DUPLICATE')], max_length=50),
        ),
        migrations.AlterField(
            model_name='contentwatcher',
            name='source_type',
            field=models.CharField(choices=[('Youtube', 'Youtube'), ('Bandcamp', 'Bandcamp'), ('Other', 'Other')], max_length=50),
        ),
    ]