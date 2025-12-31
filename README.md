# Food Nutrition (NutriLog)

A compact Django app to log meals and get fast calorie/macros analytics.

Quick facts
- Framework: Django
- DB (development): SQLite (`db.sqlite3`)
- Models: `Recipe` and `Nutrition` are persisted in the DB; management commands available to import/add records
- Optional: Image detection via external YOLO microservice (configure `YOLO_API_URL`) 

---

## Quick start (short & exact)
1. Download the repo (clone or ZIP).
2. Create & activate virtualenv (PowerShell):
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
3. Install dependencies:
   pip install -r requirements.txt
4. Run migrations:
   python manage.py migrate
5. (Optional) Create a superuser for your environment:
   python manage.py createsuperuser
6. Start dev server:
   python manage.py runserver
7. Open http://127.0.0.1:8000/

This should do: migrations + (optional) createsuperuser + runserver — app runs locally.

---

- `/admin/` → Django admin site

---

## Models (summary)

- Profile
  - user: OneToOneField(User)
  - sex: CharField (choices)
  - age: IntegerField
  - height_cm: FloatField
  - weight_kg: FloatField
  - helper methods: `bmi()`, `bmr()`, `ideal_weight_kg()`

- MealLog
  - user: ForeignKey(User)
  - meal_name: CharField
  - meal_type: CharField (Breakfast/Lunch/Dinner/Snack/Other)
  - calories: FloatField
  - protein_g / fat_g / carbs_g / fiber_g: FloatFields
  - items_json: TextField (serialized item list)
  - created_at: DateTimeField(auto_now_add=True)
  - running_calories: FloatField (computed running totals)
  - day_goal_achieved: BooleanField

- Recipe
  - name: CharField
  - slug: SlugField (unique, used for lookups)
  - ingredients: JSONField (ingredient name → grams per recipe)
  - notes: TextField (optional)
  - created_at: DateTimeField(auto_now_add=True)
  - Usage: recipes are used to compute nutrition for composite dishes via `calculate_nutrition_from_recipe()`.

- Nutrition
  - food_name: CharField
  - per-100g fields: `calories`, `protein_g`, `fat_g`, `carbs_g`, `fiber_g` (FloatFields)
  - source: CharField (optional)
  - updated_at: DateTimeField(auto_now=True)
  - Usage: per-ingredient nutrition is applied (scaled by grams) when no recipe exists via `calculate_nutrition_for_raw_ingredient()`.

These fields are used by the analytics views to compute series, totals, heatmaps and goal hit rates.

---

## Workflow / How the app works (high level)

1. User registers / logs in and can set their profile (age, sex, height, weight).
2. On the dashboard users can upload a food image (optional) — a remote YOLO microservice (configurable via `YOLO_API_URL`) predicts probable foods.
3. Detected items are turned into nutrition data (via `recipe.py` / `nutrition.py`) and saved as `MealLog` entries. When prompted for weights, any empty weight field is ignored (leave it blank to skip a detected item).
4. `analytics` / `history` views compute summaries, trends, heatmaps and per-day flags (goal achieved) using `MealLog` data.
5. Users can export CSV of their logs from the history/analytics page.

---

## Notable features (recent)
- **DB models for food data**: Added `Recipe` and `Nutrition` models so recipes and per-ingredient nutrition are persisted in the database (no file fallbacks required).
- **Import helpers**: Management commands are available to populate the DB:
  - `python manage.py import_recipes data/recipe.txt` — import many recipes from a text file
  - `python manage.py add_recipe "Dish Name" "ingredient=grams,..."` — add a single recipe
  - `python manage.py import_nutrition path/to/nutrition.xlsx` — import nutrition data from Excel
  - `python manage.py add_nutrition "Food" --calories 100 --protein 3` — add one nutrition record
- **Upload & camera capture**: Dashboard has an `Upload Food` button and a Camera mode (getUserMedia). Captured photos are converted and auto-submitted to the upload form.
- **Ignore detected items easily**: Weight inputs are optional — **leave a weight blank** to ignore a detected item; only filled weights are counted when computing totals.
- **Daily goal celebration**: When your saved meal pushes the day's total over the user's goal (BMR-based or default), a celebratory modal (emoji + confetti) appears and auto-closes after 5s.
- **Analytics UI**: History/Analytics panels now show **Remaining to goal** and BMR in the stats area; cards are arranged in two columns for consistent alignment.
- **UI consistency & polish**: Unified `.muted-btn` styles, profile dropdown hover, and compact `.streak-badge` visuals across dashboard, history, profile, and logs pages.

---

## Setup & Run (Windows example)

1. Download the repo (clone or download ZIP and extract):

   [git clone https://github.com/<your-repo>/food_nutrition.git](https://github.com/syedamashs/NutriLog.git)

   or download ZIP and extract.

2. Create and activate a virtual environment (Windows PowerShell):

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # PowerShell
   # or
   .\.venv\Scripts\activate.bat  # cmd.exe

3. Install dependencies

   - If the project provides `requirements.txt`:

     pip install -r requirements.txt

4. Apply migrations and create a superuser

   python manage.py migrate
   python manage.py createsuperuser

   # Optional: if you have nutrition/recipe data to import
   # python manage.py import_recipes data/recipe.txt
   # python manage.py import_nutrition path/to/nutrition.xlsx


5. (Optional) Collect static files for production

   python manage.py collectstatic

6. Run the development server

   python manage.py runserver

7. Visit http://127.0.0.1:8000/ in your browser. Login via `/login/` or open the admin at `/admin/`.

8. Run tests

   python manage.py test

---

## Notes & Tips

- Database: this project uses SQLite by default (`db.sqlite3`) — good for development. For production, switch to PostgreSQL or another DB and update `food_nutrition/settings.py`.
- Media & uploads: the `media/` folder is included; ensure `MEDIA_ROOT`/`MEDIA_URL` are set for production and served appropriately.
- Image detection: predictions are performed by an external Hugging Face Space (YOLO microservice). Set `YOLO_API_URL` to the full predict endpoint (for example: `https://amashtce-food-yolo-api.hf.space/predict`). Installing `ultralytics` or keeping a local model is no longer required.
- If you plan to deploy, remember to set `DEBUG=False`, configure `ALLOWED_HOSTS`, and set a secure `SECRET_KEY`.

---

