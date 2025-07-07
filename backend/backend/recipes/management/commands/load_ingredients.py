import json
import os

from django.db import models
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

class Command(BaseCommand):
    help = "Загружает ингредиенты из файла JSON в базу данных."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="data/ingredients.json",
            help="Путь к JSON-файлу с ингредиентами",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Размер пакета для bulk_create (по умолчанию: 500)",
        )

    def handle(self, *args, **options):
        file_path = options["path"]
        batch_size = options["batch_size"]

        if not os.path.exists(file_path):
            self.stderr.write(self.style.ERROR(f"Файл не найден: {file_path}"))
            return

        try:
            with open(file_path, encoding="utf-8") as file:
                ingredients_data = json.load(file)
        except json.JSONDecodeError as error:
            self.stderr.write(self.style.ERROR(f"JSON ошибка: {error}"))
            return
        except Exception as error:
            self.stderr.write(self.style.ERROR(f"Ошибка чтения файла: {error}"))
            return

        existing_ingredients = set(
            Ingredient.objects.annotate(
                name_lower=models.functions.Lower('name'),
                unit_lower=models.functions.Lower('measurement_unit')
            ).values_list('name_lower', 'unit_lower')
        )

        new_ingredients = []
        total_items = len(ingredients_data)
        processed = 0
        skipped = 0
        added = 0

        self.stdout.write(self.style.SUCCESS(f"Начата обработка {total_items} ингредиентов..."))

        for item in ingredients_data:
            processed += 1
            name = item["name"]
            unit = item["measurement_unit"]

            key = (name.lower(), unit.lower())

            if key in existing_ingredients:
                skipped += 1
                continue

            new_ingredients.append(Ingredient(name=name, measurement_unit=unit))
            existing_ingredients.add(key)
            added += 1

            if processed % 100 == 0 or processed == total_items:
                percent = processed / total_items * 100
                self.stdout.write(
                    self.style.WARNING(
                        f"Обработано: {processed}/{total_items} ({percent:.1f}%) | "
                        f"Добавлено: {added} | Пропущено: {skipped}"
                    ),
                    ending='\r'
                )
                self.stdout.flush()

        if new_ingredients:
            try:
                Ingredient.objects.bulk_create(new_ingredients, batch_size=batch_size)
                self.stdout.write("\n" + self.style.SUCCESS(
                    f"Успешно добавлено {added} новых ингредиентов! "
                    f"Пропущено дубликатов: {skipped}"
                ))
            except Exception as error:
                self.stderr.write("\n" + self.style.ERROR(
                    f"Ошибка при массовом создании: {error}"
                ))
        else:
            self.stdout.write("\n" + self.style.SUCCESS(
                "Нет новых ингредиентов для добавления. Все данные уже существуют в базе."
            ))
