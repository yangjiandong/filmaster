#! -!- coding: utf-8 -!-

from film20.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(*args, **kw):
        from film20.showtimes.models import Channel
        import datetime;

        DAYS_BACK = 0
        if len(args) > 1:
            DAYS_BACK = int(args[1])

        today=datetime.date.today()

        cinemas = Channel.objects.theaters().filter(last_screening_time__lte=today, last_screening_time__gte=today-datetime.timedelta(days=DAYS_BACK))
        cinemas = cinemas.order_by('town__country', '-last_screening_time')

        for c in cinemas:
            print "%-2s %-20s %-40s %s" % (c.town.country.code, c.town, c.name[:40], c.last_screening_time)
