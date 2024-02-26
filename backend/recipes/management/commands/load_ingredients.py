import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда загрузки ингридиентов."""
    def handle(self, *args, **kwargs):
        with open(
                'recipes/data/ingredients.json', 'r',
                encoding='UTF-8'
        ) as ingredients_file:
            ingredient_data = json.loads(ingredients_file.read())
            total_count = 0
            for ingredients in ingredient_data:
                instance, created = Ingredient.objects.get_or_create(
                    **ingredients
                )
                if created:
                    total_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'Данные загружены в количестве {total_count}')
            )
