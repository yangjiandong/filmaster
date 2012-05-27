from django.core.management.base import BaseCommand, CommandError
from film20.core.models import Film
from film20.utils.cache_helper import *

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **opts):
        for film in Film.objects.iterator():
            delete_cache(CACHE_RELATED_FILMS, film.id)
            