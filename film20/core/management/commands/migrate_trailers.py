from django.db.models import Q
from django.conf import settings
from django.core.management.base import BaseCommand

from film20.core.models import Film, Trailer
from film20.externallink.models import ExternalLink

sl = lambda l: 'en' if l == 'pl' else 'pl'

class Command( BaseCommand ):
    def handle( self, *args, **options ):

        Trailer.all_objects.all().delete()
        links = ExternalLink.all_objects.filter( url_kind=ExternalLink.TRAILER ).order_by( '-created_at' )
        print "links to migrate:", len( links )

        for link in links:

            LANG = link.LANG
            SECOND_LANG = sl( LANG )


            try:
                trailer = Trailer.all_objects.get( object=link.film, url=link.url, LANG=LANG )
            except Trailer.DoesNotExist:

                second_lang_trailers = ExternalLink.all_objects.filter( url_kind=ExternalLink.TRAILER, film=link.film, LANG=SECOND_LANG )
                if len( second_lang_trailers ) == 0:
                    already_assigned = Trailer.all_objects.filter( object=link.film, LANG=SECOND_LANG ).count() > 0
                    if not already_assigned:
                        LANG=None # assign to all versions

                try:
                    trailer = Trailer.all_objects.get( object=link.film, url=link.url, LANG=LANG )
                except Trailer.DoesNotExist:
                    trailer = Trailer(
                        LANG=LANG,
                        object=link.film,
                        url=link.url,
                        added_by = link.user,
                        date_added = link.created_at,
                        moderation_status = link.moderation_status,
                        moderation_status_at = link.moderation_status_at,
                        moderation_status_by = link.moderation_status_by
                    )
                    trailer.save( skip_activity=True )
