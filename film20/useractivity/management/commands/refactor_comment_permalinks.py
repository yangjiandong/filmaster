from django.core.management.base import BaseCommand
from django.conf import settings
from film20.useractivity.models import UserActivity
from film20.config.urls import *
import logging
import string

logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **opts):
        """
            Remove old permalinks for short_review activity,
            and replace them with new ones
        """

        acts = UserActivity.objects.select_related()\
                        .filter(activity_type=UserActivity.TYPE_COMMENT).order_by("-id")

        for act in acts.iterator():
            content_object = act.comment.content_object # this throws an exception for old comments related with the deleted Thread model

            from film20.forum.models import Thread
            if isinstance(content_object, Thread):
                # do not touch the permalinks, just do a hack for slugs
                act.slug = 'LEGACY_FORUM_COMMENT'
            else:
                if settings.ENSURE_OLD_STYLE_PERMALINKS:
                    act.permalink = act.comment.get_absolute_url_old_style()
                else:
                    act.permalink = act.comment.get_absolute_url()
                act.slug = act.comment.get_slug()                
                act.subdomain = act.comment.get_subdomain()                
            act.save() 
