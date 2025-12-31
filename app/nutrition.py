from .models import Nutrition


def calculate_nutrition_from_recipe(recipe_dict, user_grams):
    # recipe_dict = proportional grams (NOT final grams)
    recipe_total = sum(recipe_dict.values())

    if recipe_total <= 0:
        return None

    scale = user_grams / recipe_total

    totals = {
        "calories": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "carbs_g": 0.0,
        "fiber_g": 0.0
    }

    try:
        for ingredient, base_grams in recipe_dict.items():
            try:
                ni = Nutrition.objects.get(ingredient=ingredient)
            except Nutrition.DoesNotExist:
                # ingredient not found in DB -> skip
                continue

            actual_grams = base_grams * scale
            factor = actual_grams / 100.0

            totals["calories"] += ni.calories * factor
            totals["protein_g"] += ni.protein_g * factor
            totals["fat_g"] += ni.fat_g * factor
            totals["carbs_g"] += ni.carbs_g * factor
            totals["fiber_g"] += ni.fiber_g * factor

        for k in totals:
            totals[k] = round(totals[k], 2)

        return totals
    except Exception:
        # If DB access fails, return None
        return None


NUTRIENT_COLS = ["calories", "protein_g", "fat_g", "carbs_g", "fiber_g"]


def calculate_nutrition_for_raw_ingredient(ingredient, grams):
    """
    ingredient: raw ingredient name (e.g. carrot)
    grams: consumed grams
    """
    try:
        ni = Nutrition.objects.get(ingredient=ingredient)
    except Nutrition.DoesNotExist:
        return None
    except Exception:
        return None

    totals = {}
    for col in NUTRIENT_COLS:
        val = getattr(ni, col)
        totals[col] = round((val * grams) / 100.0, 2)

    return totals