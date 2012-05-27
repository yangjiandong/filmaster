from film20.core.management.base import BaseCommand
from django.conf import settings

import logging
logger=logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **kw):
        from film20.recommendations.bot_helper import do_update_films_popularity
        do_update_films_popularity()
