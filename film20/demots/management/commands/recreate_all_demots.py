from django.core.management.base import BaseCommand, CommandError
from film20.demots.models import Demot

class Command( BaseCommand ):
    help = "Recreates all demots"

    def handle( self, **options ):
        for demot in Demot.objects.all():
            demot.final_image = None
            demot.remove_thumbnail()
            demot.save()
