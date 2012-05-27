from film20.core.management.base import BaseCommand
from django.contrib.auth.models import User
from film20.core.models import Profile

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **opts):
        for u in User.objects.filter(profile__recommendations_status=2):
            logger.info('computing fast recommendations for %s', u)
            compute_fast_recommendations(u.id, True)

            