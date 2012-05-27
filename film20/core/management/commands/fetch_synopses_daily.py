from film20.core.management.base import BaseCommand
from django.conf import settings
from film20.recommendations.bot_helper import fetch_synopses_for_recently_imported_films, fetch_synopses_for_recently_imported_films_no_synopsis

import logging
logger=logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **kw):
        if settings.LANGUAGE_CODE == 'pl':
            fetch_synopses_for_recently_imported_films(fetcher="fdb")
            fetch_synopses_for_recently_imported_films_no_synopsis(fetcher="filmweb")
        else:
            fetch_synopses_for_recently_imported_films(fetcher="enwikipedia")
            fetch_synopses_for_recently_imported_films_no_synopsis(fetcher="rottentomatoes")
