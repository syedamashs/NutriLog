# Food Nutrition (NutriLog)

A compact Django app to log meals and get fast calorie/macros analytics.

Quick facts
- Framework: Django
- DB (development): SQLite (`db.sqlite3`)
- Optional: YOLO (ultralytics) for image-based detection

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

These fields are used by the analytics views to compute series, totals, heatmaps and goal hit rates.

---

## Workflow / How the app works (high level)

1. User registers / logs in and can set their profile (age, sex, height, weight).
2. On the dashboard users can upload a food image (optional) — YOLO model predicts probable foods.
3. Detected items are turned into nutrition data (via `recipe.py` / `nutrition.py`) and saved as `MealLog` entries.
4. `analytics` / `history` views compute summaries, trends, heatmaps and per-day flags (goal achieved) using `MealLog` data.
5. Users can export CSV of their logs from the history/analytics page.

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
- YOLO model: `ml/food_yolo.pt` is required for image-based predictions; if you don't need image detection you can skip installing `ultralytics` and the model will not be used.
- If you plan to deploy, remember to set `DEBUG=False`, configure `ALLOWED_HOSTS`, and set a secure `SECRET_KEY`.

---

