import logging
logger = logging.getLogger(__name__)
from optparse import make_option
import datetime

from film20.core.management.base import BaseCommand
from django.db import models

from film20.import_films.imdb_fetcher import save_film_poster
from film20.core.models import Film

class Command(BaseCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--all',
                    default=None,
                    dest = 'all',
                    action='store_true',
                    help='Fetch all posters for all films - don\'t check tmdb_import_status'
        ),
        make_option('--permalinks',
                    default=None,
                    dest = 'permalinks',
                    action = 'store_true',
                    help='Fetch posters for provided films',
        ),
    )

    def handle(self, *args, **opts):
        self.opts = opts
        if opts.get('permalinks'):
            films = Film.objects.filter(permalink__in=args)
        elif opts.get('all'):
            films = Film.objects.all()
        else:
#            query = models.Q(hires_image="") | models.Q(hires_image__isnull=True)
#            films = Film.objects.filter(query)
            films = Film.objects.filter(tmdb_import_status=Film.NOT_IMPORTED)
        
        films = films.order_by('-popularity')

        playing_ids = Film.objects.filter(
                filmonchannel__screening__utc_time__gt=datetime.datetime.now()
        ).values_list('id', flat=True)
        playing_ids = list(playing_ids.distinct())
        
        from itertools import chain
        
        for (i, film) in enumerate(chain(films.filter(id__in=playing_ids),
                                         films.exclude(id__in=playing_ids))):
            logger.info("%d - %r", i, film)
            try:
                save_film_poster(film)
            except Exception, e:
                logger.exception(e)

