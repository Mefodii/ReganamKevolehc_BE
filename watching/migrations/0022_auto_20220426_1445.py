# Generated by Django 3.1.7 on 2022-04-26 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0021_auto_20220426_1443'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='check_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
