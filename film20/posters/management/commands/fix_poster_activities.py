from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from film20.useractivity.models import UserActivity

class Command( BaseCommand ):
    help = "Fix poster activities.."

    def handle( self, **options ):
        for ua in UserActivity.objects.filter( activity_type=UserActivity.TYPE_POSTER ):
            if ua.person:
                ua.object_title = str( ua.person )
                ua.object_slug = ua.person.permalink
                ua.save()

