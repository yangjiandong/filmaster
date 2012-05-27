from film20.core.management.base import BaseCommand
from film20.core.models import Film
from film20.useractivity.models import UserActivity
from django.db.models import Q

class Command(BaseCommand):
    def handle(*args, **kw):
        films = Film.objects.filter(objectlocalized__tagged_items__tag__name__in=args).values_list('id', flat=True).distinct()
        
        query = Q(film__in=films)
        query = query | Q(post__related_film__in=films)
        query = query | Q(short_review__parent__in=films)

        items = UserActivity.objects.filter(query).distinct()
        total = items.count()
        for i, ua in enumerate(items):
            print i+1, '/', total
            ua.update_tags()


