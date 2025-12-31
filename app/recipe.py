from .models import Recipe


def get_recipe(dish_name):
    """Return dict of ingredient->grams by looking up `Recipe` model only.

    - Looks up by slug first, then by name.
    - Returns the ingredients dict (ingredient -> grams float) or None if not found.
    """
    # Expect dish_name to be either slug or exact name
    try:
        r = Recipe.objects.filter(slug=dish_name).first() or Recipe.objects.filter(name=dish_name).first()
        if r:
            return r.ingredients
    except Exception:
        # If DB access fails, return None (no fallback to file)
        return None
    return None
