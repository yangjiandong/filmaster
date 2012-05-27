from django.core.management.base import BaseCommand, CommandError
from film20.import_ratings.import_ratings_helper import import_ratings

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **opts):
        import_ratings()
