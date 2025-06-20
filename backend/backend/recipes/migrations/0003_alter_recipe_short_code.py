# Generated by Django 4.2 on 2025-06-17 18:05

from django.db import migrations, models
import shortuuid.main


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_alter_ingredient_measurement_unit_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='short_code',
            field=models.CharField(default=shortuuid.main.ShortUUID.uuid, max_length=22, unique=True, verbose_name='Короткий код'),
        ),
    ]
