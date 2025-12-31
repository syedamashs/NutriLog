from django.core.management.base import BaseCommand, CommandError
from app.models import Nutrition

class Command(BaseCommand):
    help = 'Add or update a single nutrition row. Usage: manage.py add_nutrition "ingredient" calories protein_g fat_g carbs_g fiber_g'

    def add_arguments(self, parser):
        parser.add_argument('ingredient', type=str, help='Ingredient name')
        parser.add_argument('calories', type=float)
        parser.add_argument('protein_g', type=float)
        parser.add_argument('fat_g', type=float)
        parser.add_argument('carbs_g', type=float)
        parser.add_argument('fiber_g', type=float)

    def handle(self, *args, **options):
        ingredient = options['ingredient'].strip()
        data = {
            'calories': options['calories'],
            'protein_g': options['protein_g'],
            'fat_g': options['fat_g'],
            'carbs_g': options['carbs_g'],
            'fiber_g': options['fiber_g'],
        }

        obj, created = Nutrition.objects.update_or_create(ingredient=ingredient, defaults=data)
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created nutrition row for '{ingredient}'"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated nutrition row for '{ingredient}'"))
        self.stdout.write(self.style.SUCCESS(str(data)))