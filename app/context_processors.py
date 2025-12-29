from zoneinfo import ZoneInfo
from django.utils import timezone
from .logs import date_range_series

TZ = ZoneInfo('Asia/Kolkata')


def streak(request):
    """Context processor providing current streak for authenticated users.
    Streak definition: consecutive local-calendar days up to today with at least one meal logged.
    """
    if not request.user or not request.user.is_authenticated:
        return {}

    # check last 365 days (sane bound)
    days = 365
    series = date_range_series(request.user, days=days)
    # build a set of ISO dates where calories > 0
    active_dates = {s['date'].isoformat() for s in series if s['calories'] > 0}

    # get today's local date
    today = timezone.localtime(timezone.now(), TZ).date()
    # compute streak backwards
    streak_count = 0
    for i in range(days):
        d = (today - timezone.timedelta(days=i)).isoformat()
        if d in active_dates:
            streak_count += 1
        else:
            break

    # quick badge color ramp similar to leetcode (small, medium, large)
    if streak_count >= 30:
        color = '#ff7a00'  # blazing orange
    elif streak_count >= 7:
        color = '#ffb347'  # warm orange
    elif streak_count > 0:
        color = '#ffd1a4'  # light orange
    else:
        color = '#6b7280'  # gray (no streak)

    return {'streak': {'count': streak_count, 'color': color}, 'streak_date': today.isoformat()}