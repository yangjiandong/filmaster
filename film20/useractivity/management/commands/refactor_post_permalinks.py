from django.core.management.base import BaseCommand
from django.conf import settings
from film20.useractivity.models import UserActivity
import logging


logger = logging.getLogger(__name__)

class Command(BaseCommand):

    def handle(self, *args, **opts):
        """
            Remove old permalinks with subdomains for blog activity,
            and replace them with new ones
        """

        acts = UserActivity.objects.select_related().filter(activity_type=UserActivity.TYPE_POST)

        for act in acts.iterator():
            if settings.ENSURE_OLD_STYLE_PERMALINKS:
                act.permalink = act.post.get_absolute_url_old_style()
            else:
                act.permalink = act.post.get_absolute_url()
            act.slug = act.post.get_slug()
            act.subdomain = act.post.get_subdomain()

            main_related_film = act.post.get_main_related_film()
            if main_related_film:
                act.film = main_related_film
                act.film_title = main_related_film.get_title()
                act.film_permalink = main_related_film.permalink
            else:
                act.film = None
                act_film_title = None
                act.film_permalink = None

            act.save()
