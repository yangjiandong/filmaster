from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, F
from django.conf import settings
from optparse import make_option
import logging
logger = logging.getLogger(__name__)
from film20.showtimes.models import Town, FilmOnChannel, Screening
from film20.filmbasket.models import BasketItem
from django.contrib.auth.models import User
from decimal import Decimal
import datetime, time
from film20.showtimes.showtimes_helper import *
from django.core.urlresolvers import reverse
from django.conf import settings

class Command(BaseCommand):
    help = ''
    option_list = BaseCommand.option_list + (
      make_option('--debug',
                  action='store_true',
                  dest='debug',
                  default=False,
      ),
      make_option('--rematch',
                  action='store_true',
                  dest='rematch',
                  default=False,
                  help='Tries to rematch movies',
      ),
      make_option('--days',
                  dest='days',
                  default=0,
                  type='int',
      ),
    )

    def rematch(self):
        days = self.opts.get('days')
        from film20.showtimes.models import UNMATCHED, MATCHED, FilmOnChannel
        movies = FilmOnChannel.objects.filter(match=UNMATCHED)
        if days:
            since = datetime.date.today() - datetime.timedelta(days=days)
            movies = movies.filter(created_at__gte=since)
            
        logger.debug("%s movies to rematch", len(movies))
        cnt = 0
        for movie in movies:
            movie.match_and_save()
            if movie.match==MATCHED:
                logger.info("%s: matched", movie)
                cnt += 1
        if cnt:
            logger.info("%s movies has been matched", cnt)

    def handle(self, *args, **opts):
        self.opts = opts
        if opts.get('rematch'):
            self.rematch()
