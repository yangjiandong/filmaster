from django.core.management.base import BaseCommand
from django.conf import settings
from film20.useractivity.models import UserActivity
from film20.core.models import ShortReview
import logging


logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **opts):
        """
            Remove old permalinks for short_review activity,
            and replace them with new ones
        """

        acts = UserActivity.objects.select_related()\
                        .filter(activity_type=UserActivity.TYPE_SHORT_REVIEW)

        for act in acts.iterator():
            if settings.ENSURE_OLD_STYLE_PERMALINKS:
                act.permalink = act.short_review.get_absolute_url_old_style()
            else:
                act.permalink = act.short_review.get_absolute_url()
            act.slug = act.short_review.get_slug()
            act.subdomain = act.short_review.get_subdomain()
            # http://jira.filmaster.org/browse/FLM-1464
            if act.short_review.rating:
                act.rating = act.short_review.rating.rating
            act.save()
