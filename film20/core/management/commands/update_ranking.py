from itertools import groupby
from decimal import Decimal

from film20.core.management.base import BaseCommand
from film20.core.models import Rating, FilmRanking

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    
    def update_ranking(self, type, film_id, actor_id, avg, count):
        if actor_id:
            extra = {'actor_id': actor_id}
        else:
            extra = {'actor__isnull': True}

        try:
            r, created = FilmRanking.objects.get_or_create(
                    type=type,
                    film_id=film_id,
                    defaults={'average_score':avg, 'number_of_votes': count},
                    **extra)
            if not created:
                r.average_score = avg
                r.number_of_votes = count
                r.save()
        except FilmRanking.MultipleObjectsReturned:
            if actor_id:
                extra = {'actor': actor_id}
            else:
                extra = {'actor__isnull': True}
            FilmRanking.objects.filter(
                    type=type,
                    film=film_id,
                    **extra).delete()
            FilmRanking.objects.create(
                    type=type,
                    film_id=film_id,
                    actor_id=actor_id,
                    average_score=avg,
                    number_of_votes=count)

    def handle(self, *args, **kw):
        for g, items in groupby(Rating.objects.filter(rating__isnull=False, film__isnull=False).order_by('type', 'film', 'actor').values_list('type', 'film', 'actor', 'rating'), lambda v:v[:3]):
            items = list(items)
            type, film_id, actor_id = g
            avg = sum(i[3] for i in items) / Decimal(len(items))
            logger.debug("%r - %2.1f / %s", g, avg, len(items))
            self.update_ranking(type, film_id, actor_id, avg, len(items))


