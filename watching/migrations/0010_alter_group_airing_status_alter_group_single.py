# Generated by Django 4.0.4 on 2022-08-15 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('watching', '0009_alter_group_airing_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='airing_status',
            field=models.CharField(blank=True, choices=[('Ongoing', 'Ongoing'), ('Completed', 'Completed')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='group',
            name='single',
            field=models.BooleanField(default=False),
        ),
    ]
