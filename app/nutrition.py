import pandas as pd

df = pd.read_excel("data/nutrition.xlsx")

def calculate_nutrition_from_recipe(recipe_dict, user_grams):
    # recipe_dict = proportional grams (NOT final grams)
    recipe_total = sum(recipe_dict.values())

    scale = user_grams / recipe_total

    totals = {
        "calories": 0.0,
        "protein_g": 0.0,
        "fat_g": 0.0,
        "carbs_g": 0.0,
        "fiber_g": 0.0
    }

    for ingredient, base_grams in recipe_dict.items():
        row = df[df["ingredient"] == ingredient]

        if row.empty:
            continue

        actual_grams = base_grams * scale
        factor = actual_grams / 100.0

        totals["calories"] += row.iloc[0]["calories"] * factor
        totals["protein_g"] += row.iloc[0]["protein_g"] * factor
        totals["fat_g"] += row.iloc[0]["fat_g"] * factor
        totals["carbs_g"] += row.iloc[0]["carbs_g"] * factor
        totals["fiber_g"] += row.iloc[0]["fiber_g"] * factor

    for k in totals:
        totals[k] = round(totals[k], 2)

    return totals


NUTRIENT_COLS = ["calories", "protein_g", "fat_g", "carbs_g", "fiber_g"]

def calculate_nutrition_for_raw_ingredient(ingredient, grams):
    """
    ingredient: raw ingredient name (e.g. carrot)
    grams: consumed grams
    """
    row = df[df["ingredient"] == ingredient]

    if row.empty:
        return None

    totals = {}
    for col in NUTRIENT_COLS:
        val = row.iloc[0][col]
        totals[col] = round((val * grams) / 100.0, 2)

    return totals