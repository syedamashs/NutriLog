from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from .yolo import predict_foods
from .recipe import get_recipe
from .nutrition import (
    calculate_nutrition_from_recipe,
    calculate_nutrition_for_raw_ingredient
)
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    context = {}

    # STEP 1: IMAGE UPLOAD → DETECT ITEMS
    if request.method == "POST" and "image" in request.FILES:
        image = request.FILES["image"]

        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        image_path = fs.path(filename)

        foods = predict_foods(image_path)

        context = {
            "detected_items": foods
        }

    # STEP 2: WEIGHTS SUBMITTED → CALCULATE NUTRITION
    elif request.method == "POST" and "detected_items" in request.POST:
        foods = request.POST.getlist("detected_items")

        items = []
        total = {
            "calories": 0,
            "protein_g": 0,
            "fat_g": 0,
            "carbs_g": 0,
            "fiber_g": 0
        }

        for food in foods:
            grams = float(request.POST.get(f"grams_{food}", 0))

            recipe = get_recipe(food)
            if recipe:
                nutrition = calculate_nutrition_from_recipe(recipe, grams)
            else:
                nutrition = calculate_nutrition_for_raw_ingredient(food, grams)

            if nutrition:
                items.append({
                    "food": food,
                    "grams": grams,
                    "nutrition": nutrition
                })

                for k in total:
                    total[k] += nutrition[k]

        for k in total:
            total[k] = round(total[k], 2)

        context = {
            "items": items,
            "total": total
        }

    return render(request, "dashboard.html", context)
