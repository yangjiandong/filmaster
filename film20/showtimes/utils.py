import pytz
import datetime
from django.conf import settings

DAY_START_DELTA = datetime.timedelta(hours=settings.DAY_START_HOUR)

def day_start(tm):
    return (tm - DAY_START_DELTA).replace(second=0, microsecond=0, minute=0, hour=0) + DAY_START_DELTA

def get_today(timezone):
    today = day_start(datetime.datetime.now(timezone))
    return today

def parse_date(request, date):
    date = datetime.datetime.strptime(date, "%Y-%m-%d")
    return request.timezone.localize(date) + DAY_START_DELTA

def get_date(request):
    date = request.GET.get('date')
    if date:
        date = parse_date(request, date)
    else:
        date = get_today(request.timezone)
    return date

def get_available_showtime_dates(request, n=7):
    today = get_today(request.timezone)
    return [ today + datetime.timedelta(days=i) for i in range(n)]
