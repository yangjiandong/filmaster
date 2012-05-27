from film20.core.management.base import BaseCommand
from film20.core.models import Film
from film20.useractivity.models import UserActivity
from django.db.models import Q

class Command(BaseCommand):
    def handle(*args, **kw):
        query = UserActivity.objects.filter(Q(short_review__isnull=False) | Q(film__isnull=False))
        total = query.count()
        for i, ua in enumerate(query):
            ua._update_tags = False
            print '%s / %s' % (i+1, total)
            ua.save()

