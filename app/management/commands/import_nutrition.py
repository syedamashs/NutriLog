from django.core.management.base import BaseCommand, CommandError
from app.models import Nutrition
import os
import pandas as pd

class Command(BaseCommand):
    help = 'Import nutrition values from an Excel file (expects columns: ingredient, calories, protein_g, fat_g, carbs_g, fiber_g)'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default='data/nutrition.xlsx', help='Path to Excel file')
        parser.add_argument('--dry-run', action='store_true', help='Parse and print without saving')

    def handle(self, *args, **options):
        path = options['path']
        dry_run = options['dry_run']

        if not os.path.exists(path):
            raise CommandError(f"File not found: {path}")

        df = pd.read_excel(path)

        required_cols = {'ingredient', 'calories', 'protein_g', 'fat_g', 'carbs_g', 'fiber_g'}
        if not required_cols.issubset(set(df.columns)):
            raise CommandError(f"Excel file missing required columns. Found: {list(df.columns)}")

        created = 0
        updated = 0
        skipped = 0

        for _, row in df.iterrows():
            try:
                ingredient = str(row['ingredient']).strip()
                if not ingredient:
                    skipped += 1
                    continue
                data = {
                    'calories': float(row.get('calories') or 0.0),
                    'protein_g': float(row.get('protein_g') or 0.0),
                    'fat_g': float(row.get('fat_g') or 0.0),
                    'carbs_g': float(row.get('carbs_g') or 0.0),
                    'fiber_g': float(row.get('fiber_g') or 0.0),
                }

                if dry_run:
                    self.stdout.write(f"Would import: {ingredient} -> {data}")
                    continue

                obj, created_flag = Nutrition.objects.update_or_create(
                    ingredient=ingredient,
                    defaults=data
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Skipping row due to error: {e}"))
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f"Import complete: created={created}, updated={updated}, skipped={skipped}"))