from collections import defaultdict
from zoneinfo import ZoneInfo
from django.utils import timezone

from .models import MealLog

TZ = ZoneInfo('Asia/Kolkata')


def date_range_series(user, days=30):
    today = timezone.localtime(timezone.now(), TZ).date()
    start_date = today - timezone.timedelta(days=days - 1)
    series = []
    for i in range(days):
        d = start_date + timezone.timedelta(days=i)
        day_logs = MealLog.objects.filter(user=user)
        # filter in python by localdate (DB timezone may be UTC)
        day_logs = [l for l in day_logs if timezone.localtime(l.created_at, TZ).date() == d]
        series.append({
            'date': d,
            'calories': round(sum(l.calories for l in day_logs), 2),
            'protein_g': round(sum(l.protein_g for l in day_logs), 2),
            'fat_g': round(sum(l.fat_g for l in day_logs), 2),
            'carbs_g': round(sum(l.carbs_g for l in day_logs), 2),
        })
    return series


def meal_type_breakdown(user, start_date):
    """Rule-based meal type breakdown using local time buckets:
    Breakfast 04:00-10:59, Lunch 11:00-14:59, Snack 15:00-17:59, Dinner 18:00-22:59, Other otherwise."""
    counts = defaultdict(float)
    for l in MealLog.objects.filter(user=user):
        lt = timezone.localtime(l.created_at, TZ)
        ld = lt.date()
        if ld < start_date:
            continue
        hour = lt.hour
        if 4 <= hour < 11:
            m = 'Breakfast'
        elif 11 <= hour < 15:
            m = 'Lunch'
        elif 15 <= hour < 18:
            m = 'Snack'
        elif 18 <= hour < 23:
            m = 'Dinner'
        else:
            m = 'Other'
        counts[m] += l.calories
    # return as list of tuples (label, rounded_value) using canonical labels only
    canonical = ['Breakfast','Lunch','Snack','Dinner','Other']
    items = []
    for k in canonical:
        v = counts.get(k, 0.0)
        items.append((k, round(v, 1)))
    # trim out zero-value items for UI clarity
    items = [it for it in items if it[1] > 0]
    return items


def macros_totals(user, start_date):
    totals = {'protein_g': 0, 'fat_g': 0, 'carbs_g': 0}
    for l in MealLog.objects.filter(user=user):
        ld = timezone.localtime(l.created_at, TZ).date()
        if ld < start_date:
            continue
        totals['protein_g'] += l.protein_g
        totals['fat_g'] += l.fat_g
        totals['carbs_g'] += l.carbs_g
    return totals


def hourly_heatmap(user, start_date):
    # 7 rows (Mon-Sun) x 24 hours
    heatmap = [[0 for _ in range(24)] for _ in range(7)]
    for l in MealLog.objects.filter(user=user):
        lt = timezone.localtime(l.created_at, TZ)
        if lt.date() < start_date:
            continue
        wd = lt.weekday()
        h = lt.hour
        heatmap[wd][h] += l.calories
    return heatmap


def calendar_heatmap(user, days=30):
    """Return a LeetCode-style calendar heatmap for the last `days` days."""
    today = timezone.localtime(timezone.now(), TZ).date()
    start_date = today - timezone.timedelta(days=days - 1)
    start_wd = start_date.weekday()
    days_list = []
    max_cal = 0
    all_logs = MealLog.objects.filter(user=user)
    for i in range(days):
        d = start_date + timezone.timedelta(days=i)
        day_logs = [l for l in all_logs if timezone.localtime(l.created_at, TZ).date() == d]
        cals = round(sum(l.calories for l in day_logs), 2)
        weekday = d.weekday()
        week_index = (start_wd + i) // 7
        days_list.append({'date': d.isoformat(), 'calories': cals, 'weekday': weekday, 'week': week_index})
        if cals > max_cal:
            max_cal = cals
    weeks = max((x['week'] for x in days_list), default=0) + 1 if days_list else 0
    return {'days': days_list, 'weeks': weeks, 'max': max_cal}


def recent_logs(user, limit=100):
    return MealLog.objects.filter(user=user).order_by('-created_at')[:limit]
