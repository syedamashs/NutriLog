from django.core.management.base import BaseCommand, CommandError
from app.models import Recipe
import os
import json

class Command(BaseCommand):
    help = 'Import recipes from a text file (format: dish:: ing=grams, ing2=grams2, ...)'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default='data/recipe.txt', help='Path to the recipe text file')
        parser.add_argument('--dry-run', action='store_true', help='Parse and print what would be imported without saving')

    def handle(self, *args, **options):
        path = options['path']
        dry_run = options['dry_run']

        if not os.path.exists(path):
            raise CommandError(f"File not found: {path}")

        created = 0
        updated = 0
        skipped = 0

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    dish, ing_part = line.split('::', 1)
                except ValueError:
                    self.stdout.write(self.style.WARNING(f"Skipping invalid line: {line}"))
                    skipped += 1
                    continue

                dish = dish.strip()
                ingredients = {}
                for item in ing_part.split(','):
                    item = item.strip()
                    if not item:
                        continue
                    try:
                        name, grams = item.split('=', 1)
                        ingredients[name.strip()] = float(grams.strip())
                    except Exception:
                        self.stdout.write(self.style.WARNING(f"Skipping invalid ingredient '{item}' for dish '{dish}'"))

                if dry_run:
                    self.stdout.write(f"Would import: {dish} -> {json.dumps(ingredients)}")
                    continue

                obj, created_flag = Recipe.objects.update_or_create(
                    name=dish,
                    defaults={
                        'ingredients': ingredients
                    }
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Import complete: created={created}, updated={updated}, skipped={skipped}"))