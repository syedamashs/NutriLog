from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .yolo import predict_foods
from .recipe import get_recipe
from .nutrition import (
    calculate_nutrition_from_recipe,
    calculate_nutrition_for_raw_ingredient
)
from .models import MealLog
import json
from collections import OrderedDict
from django.db.models import Sum
from django.utils import timezone
from zoneinfo import ZoneInfo
from .logs import date_range_series, meal_type_breakdown, macros_totals, hourly_heatmap, calendar_heatmap, recent_logs


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

    # STEP 2: WEIGHTS SUBMITTED → CALCULATE + SAVE
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

        # round totals
        for k in total:
            total[k] = round(total[k], 2)

        # Determine meal type (from form or default)
        meal_type = request.POST.get('meal_type', 'Other')

        # Save items as JSON for detail view
        items_json = json.dumps(items)

        # SAVE MEAL LOG (ONE ROW PER MEAL)
        meal = MealLog.objects.create(
            user=request.user,
            meal_name=", ".join(foods),
            meal_type=meal_type,
            calories=total["calories"],
            protein_g=total["protein_g"],
            fat_g=total["fat_g"],
            carbs_g=total["carbs_g"],
            fiber_g=total["fiber_g"],
            items_json=items_json,
        )

        # Recompute whether the user's goal was achieved for this meal's date and update all logs for that day
        try:
            tz = ZoneInfo('Asia/Kolkata')
            local_date = timezone.localtime(meal.created_at, tz).date()
            day_start = timezone.datetime(local_date.year, local_date.month, local_date.day, 0, 0, 0, tzinfo=tz)
            day_end = day_start + timezone.timedelta(days=1)

            # Determine user's goal (BMR-based if available)
            goal_val = 2000
            try:
                profile = getattr(request.user, 'profile', None)
                bmr = profile.bmr() if profile else None
                if bmr:
                    goal_val = int(bmr)
            except Exception:
                goal_val = 2000

            day_total = MealLog.objects.filter(user=request.user, created_at__gte=day_start, created_at__lt=day_end).aggregate(total=Sum('calories'))['total'] or 0
            achieved = True if (day_total > 0 and day_total <= goal_val) else False
            MealLog.objects.filter(user=request.user, created_at__gte=day_start, created_at__lt=day_end).update(day_goal_achieved=achieved)
        except Exception:
            pass

        context = {
            "items": items,
            "total": total
        }

    return render(request, "dashboard.html", context)


# helper: recompute the day_goal_achieved flag for a specific date for a user
def recompute_day_goal_for_date(user, d):
    """Recompute running_calories and day_goal_achieved flags for all MealLog rows for a given user/date.
    - Builds per-day chronological running totals.
    - Once running total reaches/exceeds the user's goal, marks that row and all subsequent rows for that day as achieved.
    Returns True if the day is achieved, False otherwise.
    """
    try:
        tz = ZoneInfo('Asia/Kolkata')
        day_start = timezone.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
        day_end = day_start + timezone.timedelta(days=1)

        # determine the goal for the user (BMR if available)
        goal_val = 2000
        try:
            profile = getattr(user, 'profile', None)
            bmr = profile.bmr() if profile else None
            if bmr:
                goal_val = int(bmr)
        except Exception:
            goal_val = 2000

        # iterate logs in chronological order, compute running total and set flags
        day_logs = list(MealLog.objects.filter(user=user, created_at__gte=day_start, created_at__lt=day_end).order_by('created_at'))
        running = 0.0
        achieved_once = False
        for ml in day_logs:
            running += float(ml.calories or 0)
            # mark achieved once running >= goal_val
            if not achieved_once and running >= goal_val and running > 0:
                achieved_once = True
            ml.running_calories = round(running, 2)
            ml.day_goal_achieved = bool(achieved_once)
            ml.save()

        return bool(achieved_once)
    except Exception:
        return False
    
#History
@login_required
def history(request):
    # analytics parameters (robust parsing)
    raw_days = request.GET.get('days', None)
    try:
        days_param = int(raw_days) if raw_days is not None else 30
    except (ValueError, TypeError):
        days_param = 30
    if days_param not in (7, 14, 30):
        days_param = 30

    tz = ZoneInfo('Asia/Kolkata')
    today = timezone.localtime(now(), tz).date()
    # compute start_date for requested range (inclusive)
    start_date = today - timezone.timedelta(days=days_param-1)

    logs = list(MealLog.objects.filter(user=request.user).order_by("-created_at"))
    # logs within the requested range (used for list display and CSV export)
    logs_in_range = [l for l in logs if start_date <= timezone.localtime(l.created_at, tz).date() <= today]

    # annotate each log with a localized timestamp for display in Asia/Kolkata and a computed meal type
    MEAL_ICONS = {'Breakfast':'🍳','Lunch':'🍛','Dinner':'🍽','Snack':'🍪','Other':'🍽'}
    for _l in logs:
        try:
            _l.local_created = timezone.localtime(_l.created_at, tz)
        except Exception:
            _l.local_created = _l.created_at
        # rule-based meal type per local time
        try:
            hh = _l.local_created.hour
            if 4 <= hh < 11:
                _l.computed_type = 'Breakfast'
            elif 11 <= hh < 15:
                _l.computed_type = 'Lunch'
            elif 15 <= hh < 18:
                _l.computed_type = 'Snack'
            elif 18 <= hh < 23:
                _l.computed_type = 'Dinner'
            else:
                _l.computed_type = 'Other'
        except Exception:
            _l.computed_type = getattr(_l, 'meal_type', 'Other') or 'Other'
        _l.computed_icon = MEAL_ICONS.get(_l.computed_type, '🍽')

    # today's totals
    today_logs = [l for l in logs if timezone.localtime(l.created_at, tz).date() == today]
    total_today = {
        "calories": round(sum(l.calories for l in today_logs), 2),
        "protein_g": round(sum(l.protein_g for l in today_logs), 2),
        "fat_g": round(sum(l.fat_g for l in today_logs), 2),
        "carbs_g": round(sum(l.carbs_g for l in today_logs), 2),
        "fiber_g": round(sum(l.fiber_g for l in today_logs), 2),
    }

    # Default goal is 2000 kcal/day; if the user has a profile with a BMR estimate, use that as their personal goal
    goal = 2000
    try:
        profile = getattr(request.user, 'profile', None)
        bmr = profile.bmr() if profile else None
        if bmr:
            goal = int(bmr)
    except Exception:
        # keep default goal
        goal = 2000

    if total_today["calories"] <= goal:
        status = "under"
        diff = round(goal - total_today["calories"], 2)
    else:
        status = "over"
        diff = round(total_today["calories"] - goal, 2)

    # MEALS grouped by date for the detailed list (only include logs inside the selected range)
    grouped = OrderedDict()
    for log in logs_in_range:
        d = timezone.localtime(log.created_at, tz).date()
        grouped.setdefault(d, []).append(log)

    days = []
    MEAL_ICONS = {'Breakfast':'🍳','Lunch':'🍛','Dinner':'🍽','Snack':'🍪','Other':'🍽'}
    for d, items in grouped.items():
        meals = []
        for log in items:
            try:
                parsed_items = json.loads(log.items_json) if log.items_json else []
            except Exception:
                parsed_items = []
            hints = []
            if log.calories and (log.protein_g * 4) < (log.calories * 0.1):
                hints.append('⚠️ Low protein')
            if log.calories and (log.fat_g * 9) > (log.calories * 0.35):
                hints.append('⚠️ High fat')

            lt = timezone.localtime(log.created_at, tz)
            hour = lt.hour
            if 4 <= hour < 11:
                computed_type = 'Breakfast'
            elif 11 <= hour < 15:
                computed_type = 'Lunch'
            elif 15 <= hour < 18:
                computed_type = 'Snack'
            elif 18 <= hour < 23:
                computed_type = 'Dinner'
            else:
                computed_type = getattr(log, 'meal_type', 'Other') or 'Other'

            meals.append({
                'log': log,
                'items': parsed_items,
                'hints': hints,
                'icon': MEAL_ICONS.get(computed_type, '🍽'),
                'computed_type': computed_type,
                'local_time': lt.strftime('%H:%M (%Z)')
            })

        day_total = {
            'date': d,
            'items': meals,
            'total': {
                'calories': round(sum(i['log'].calories for i in meals), 2),
                'protein_g': round(sum(i['log'].protein_g for i in meals), 2),
                'fat_g': round(sum(i['log'].fat_g for i in meals), 2),
                'carbs_g': round(sum(i['log'].carbs_g for i in meals), 2),
                'fiber_g': round(sum(i['log'].fiber_g for i in meals), 2),
            }
        }
        days.append(day_total)

    # build timeseries for requested range (oldest->newest)
    start_date = today - timezone.timedelta(days=days_param-1)
    date_range = [(start_date + timezone.timedelta(days=i)) for i in range(days_param)]

    # Ensure running_calories and day_goal_achieved are computed for each day in the range
    # (this handles cases where logs were added/updated without triggering recompute)
    for d in date_range:
        try:
            day_start = timezone.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
            day_end = day_start + timezone.timedelta(days=1)
            day_qs = MealLog.objects.filter(user=request.user, created_at__gte=day_start, created_at__lt=day_end)
            total = day_qs.aggregate(total=Sum('calories'))['total'] or 0
            # recompute when there are logs with positive calories but running_calories still zero
            if total > 0 and day_qs.filter(running_calories=0).exists():
                recompute_day_goal_for_date(request.user, d)
        except Exception:
            pass

    series = []
    for d in date_range:
        day_logs = [l for l in logs if timezone.localtime(l.created_at, tz).date() == d]
        series.append({
            'date': d,
            'calories': round(sum(l.calories for l in day_logs), 2),
            'protein_g': round(sum(l.protein_g for l in day_logs), 2),
            'fat_g': round(sum(l.fat_g for l in day_logs), 2),
            'carbs_g': round(sum(l.carbs_g for l in day_logs), 2),
        })

    total_calories = round(sum(s['calories'] for s in series), 2)
    avg_calories = round(total_calories / days_param, 2) if days_param > 0 else 0

    # stats computed only for days with logged calories (>0)
    days_with_data = sum(1 for s in series if s['calories'] > 0)

    # Count days where the per-day goal was achieved (using the day_goal_achieved flag stored on MealLog)
    days_achieved = 0
    for d in date_range:
        try:
            day_start = timezone.datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
            day_end = day_start + timezone.timedelta(days=1)
            if MealLog.objects.filter(user=request.user, created_at__gte=day_start, created_at__lt=day_end, day_goal_achieved=True).exists():
                days_achieved += 1
        except Exception:
            continue

    # Hit rate over days with logged calories only (exclude days without logs)
    goal_hit_rate = round(days_achieved / days_with_data * 100, 1) if days_with_data > 0 else 0

    max_daily_calories = max((s['calories'] for s in series), default=0)

    # previous period comparison
    prev_start = start_date - timezone.timedelta(days=days_param)
    prev_end = start_date - timezone.timedelta(days=1)
    prev_total = 0
    for l in logs:
        ld = timezone.localtime(l.created_at, tz).date()
        if ld >= prev_start and ld <= prev_end:
            prev_total += l.calories
    prev_total = round(prev_total, 2)
    pct_change = None
    if prev_total > 0:
        pct_change = round(((total_calories - prev_total) / prev_total) * 100, 1)

    # meal-type breakdown for range (rule-based by local time)
    meal_type_items = meal_type_breakdown(request.user, start_date)  # returns sorted list of (label, calories)

    # macros totals for range
    macros_totals = {'protein_g': 0, 'fat_g': 0, 'carbs_g': 0}
    for l in logs:
        ld = timezone.localtime(l.created_at, tz).date()
        if ld < start_date: continue
        macros_totals['protein_g'] += l.protein_g
        macros_totals['fat_g'] += l.fat_g
        macros_totals['carbs_g'] += l.carbs_g

    # calendar heatmap (LeetCode-style monthly view — daily totals for the requested range)
    cal_heat = calendar_heatmap(request.user, days=days_param)

    # recent logs (limit) — limited to the selected range
    recent_logs = list(logs_in_range[:50])

    # expose profile BMR and a simple TDEE suggestion (sedentary 1.2 multiplier) when available
    profile_bmr = None
    tdee_suggestion = None
    try:
        profile = getattr(request.user, 'profile', None)
        if profile:
            profile_bmr = profile.bmr()
            if profile_bmr:
                # suggest a sedentary TDEE (simple multiplier)
                tdee_suggestion = int(round(profile_bmr * 1.2))
    except Exception:
        profile_bmr = None
        tdee_suggestion = None

    context = {
        # pass range-filtered logs to the template so the list view and CSV export reflect the selected days
        'logs': logs_in_range,
        'recent_logs': recent_logs,
        'total_today': total_today,
        'total_calories': total_calories,
        'avg_calories': avg_calories,
        'prev_total': prev_total,
        'pct_change': pct_change,
        'goal': goal,
        'profile_bmr': profile_bmr,
        'tdee_suggestion': tdee_suggestion,
        'goal_close': round(goal * 0.9, 2),
        'goal_hit_rate': goal_hit_rate,
        'status': status,
        'diff': diff,
        'days': days,
        'series': series,            # requested series for charts
        'series_days': days_param,
        'meal_type_items': meal_type_items,
        'macros_totals': macros_totals,
        'calendar_heatmap': cal_heat,
        'weekly_max_adj': max(100, round(max((s['calories'] for s in series), default=0) * 1.1, 2)),
        'days_with_data': days_with_data,
        'max_daily_calories': max_daily_calories,
        
        'now': timezone.localtime(now(), tz),
    }

    return render(request, "history.html", context)


#Analytics
@login_required
def analytics(request):
    # alias to the main analytics/history implementation
    return history(request)

#Analytics_Logs
@login_required
def analytics_logs(request):
    tz = ZoneInfo('Asia/Kolkata')
    qdate = request.GET.get('date')
    logs_qs = list(MealLog.objects.filter(user=request.user).order_by('-created_at'))
    if qdate:
        try:
            from datetime import datetime
            d = datetime.strptime(qdate, '%Y-%m-%d').date()
            logs_qs = [l for l in logs_qs if timezone.localtime(l.created_at, tz).date() == d]
        except Exception:
            pass
    # annotate with localized timestamps
    for _l in logs_qs:
        try:
            _l.local_created = timezone.localtime(_l.created_at, tz)
        except Exception:
            _l.local_created = _l.created_at
        # computed meal type
        try:
            hh = _l.local_created.hour
            if 4 <= hh < 11:
                _l.computed_type = 'Breakfast'
            elif 11 <= hh < 15:
                _l.computed_type = 'Lunch'
            elif 15 <= hh < 18:
                _l.computed_type = 'Snack'
            elif 18 <= hh < 23:
                _l.computed_type = 'Dinner'
            else:
                _l.computed_type = 'Other'
        except Exception:
            _l.computed_type = getattr(_l, 'meal_type', 'Other') or 'Other'
        _l.computed_icon = {'Breakfast':'🍳','Lunch':'🍛','Dinner':'🍽','Snack':'🍪','Other':'🍽'}.get(_l.computed_type, '🍽')
    return render(request, 'analytics_logs.html', {'logs': logs_qs, 'now': timezone.localtime(now(), tz)})
