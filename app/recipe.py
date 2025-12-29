def get_recipe(dish_name):
    """
    Returns dict: {ingredient: grams}
    """
    with open("data/recipe.txt", "r") as f:
        for line in f:
            dish, ing_part = line.strip().split("::")
            if dish == dish_name:
                ingredients = {}
                for item in ing_part.split(","):
                    name, grams = item.strip().split("=")
                    ingredients[name] = float(grams)
                return ingredients
    return None
