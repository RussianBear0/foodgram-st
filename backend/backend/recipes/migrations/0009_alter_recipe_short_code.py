# Generated by Django 4.2 on 2025-05-22 08:01

from django.db import migrations, models
import shortuuid.main


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_alter_recipe_short_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='short_code',
            field=models.CharField(default=shortuuid.main.ShortUUID.uuid, max_length=22, unique=True, verbose_name='Короткий код'),
        ),
    ]
