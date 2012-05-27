import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from film20.showtimes.models import *

print "setting cinema timezones"
for c in Cinema.objects.filter(timezone_id__isnull=True):
  c.save()

print "calculating screening UTC times"
query = Screening.objects.filter(utc_time__isnull=True, date__gte=datetime.date.today()-datetime.timedelta(days=1))
print "count:", query.count()
for s in query:
  s.save()
