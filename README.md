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

## About the DB & superuser (direct answer)

- If you commit `db.sqlite3` and someone downloads the ZIP, the file contains the database state from your repo — including user accounts and any superuser you created.
- That means your superuser account will exist in their copy only if you pushed the DB file; but **they will not know your password** unless you share it.
- Best practice: do **not** commit `db.sqlite3` to a public repo; instead, others should run migrations and create their **own** superuser with:

  python manage.py migrate
  python manage.py createsuperuser


## Files to know (short)
- `app/models.py` — `Profile`, `MealLog`
- `app/views.py` — dashboard and analytics
- `app/yolo.py` — YOLO wrapper (requires `ml/food_yolo.pt`)
- `templates/` — pages for dashboard, analytics/history, logs, profile, auth

## Tests
Run:

  python manage.py test

---

If you want, I created a `requirements.txt` file (see below). I can also remove `db.sqlite3` from the repo and add `.gitignore` if you want that cleaned up.
