from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from film20.useractivity.models import UserActivity

class Command( BaseCommand ):
    help = "Replaces 'image' to 'hires_image' in person photo"

    def handle( self, **options ):
        for ua in UserActivity.objects.filter( activity_type=UserActivity.TYPE_POSTER, 
                                               person__isnull=False ).order_by( 'created_at' ):
            ua.person.hires_image = ua.content
            ua.person.save()

