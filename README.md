# Food Nutrition (NutriLog)

A small Django app to track meals, analyze calories/macros, and provide simple analytics and logs. Users can register, log meals (manually or via image detection), view daily statistics and trends, and export their data.

---

## Tech stack

- Python (3.10+ recommended)
- Django (web framework)
- SQLite (default development database)
- Ultralitycs YOLO (for food detection) — optional GPU support if available
- Chart.js (front-end charting via CDN)

Project layout (important folders/files)
- `manage.py` — Django management CLI
- `food_nutrition/` — project settings and root URL config
- `app/` — main Django app containing views, models, templates, and utilities
  - `app/views.py` — dashboard, history/analytics, logs, helper functions
  - `app/views_auth.py` — login/register/logout
  - `app/profile.py` — profile view
  - `app/models.py` — `Profile`, `MealLog` models
  - `app/yolo.py` — wraps YOLO model (`ml/food_yolo.pt`) to predict foods from an image
  - `app/recipe.py`, `app/nutrition.py` — nutrition lookup and calculations
  - `app/logs.py` — analytics helpers (breakdowns, heatmap, totals)
- `templates/` — HTML templates (dashboard, history/analytics, logs, profile, auth pages)
- `ml/food_yolo.pt` — pretrained YOLO model file (used by `app/yolo.py`)

---

## Key endpoints

- `/` → Dashboard (main page; image upload or manual logging)
- `/login/` → Login page
- `/register/` → Register page
- `/logout/` → Logout and redirect
- `/history/` → Meal history UI (legacy name)
- `/analytics/` → Analytics page (alias of history view)
- `/analytics/logs/` → Logs page (filterable by date)
- `/profile/` → Profile page (edit weight/height/sex/age)
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

   git clone https://github.com/<your-repo>/food_nutrition.git

   or download ZIP and extract.

2. Create and activate a virtual environment (Windows PowerShell):

   python -m venv .venv
   .\.venv\Scripts\Activate.ps1   # PowerShell
   # or
   .\.venv\Scripts\activate.bat  # cmd.exe

3. Install dependencies

   - If the project provides `requirements.txt`:

     pip install -r requirements.txt

   - If not, install the main dependencies:

     pip install django ultralytics

   Note: `ultralytics` pulls in `torch` which may be large; follow the `ultralytics` / `pytorch` docs for specific CUDA builds if you need GPU support.

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

If you want, I can:
- create a `requirements.txt` file from the environment I used to run tests, or
- update templates to use the `{% url 'analytics' %}` tag everywhere for robustness.

Which one should I do next? ✅
