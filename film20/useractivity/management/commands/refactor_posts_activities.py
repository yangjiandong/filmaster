from django.core.management.base import BaseCommand
from django.conf import settings
from film20.useractivity.models import UserActivity
import logging


logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **opts):
        """
            Check if post is featured or published and setup corresponding activity as featured
        """

        notes_activities = UserActivity.objects.all_notes().select_related('post')

        for act in notes_activities:
            if act.post.featured_note or act.post.is_published:
                act.featured = True
            else:
                act.featured = False
            act.save()
