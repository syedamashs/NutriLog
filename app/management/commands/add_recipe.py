from django.core.management.base import BaseCommand, CommandError
from app.models import Recipe
import json

class Command(BaseCommand):
    help = 'Add a single recipe. Usage: manage.py add_recipe "Dish Name" "ing1=10,ing2=20"'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Recipe name')
        parser.add_argument('ingredients', type=str, help='Comma-separated ingredients, e.g. "ing1=10,ing2=20"')

    def handle(self, *args, **options):
        name = options['name'].strip()
        ing_str = options['ingredients'].strip()

        ingredients = {}
        for item in ing_str.split(','):
            item = item.strip()
            if not item:
                continue
            try:
                k, v = item.split('=', 1)
                ingredients[k.strip()] = float(v.strip())
            except Exception as e:
                raise CommandError(f"Invalid ingredient format: {item}")

        obj, created = Recipe.objects.update_or_create(name=name, defaults={'ingredients': ingredients})
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created recipe '{name}'"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated recipe '{name}'"))
        self.stdout.write(self.style.SUCCESS(f"Ingredients: {json.dumps(ingredients)}"))