from film20.core.management.base import BaseCommand
from film20.core.models import UserRatingTimeRange

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **opts):
        UserRatingTimeRange.process_rating_timerange()
            
