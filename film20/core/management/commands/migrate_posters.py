from django.db.models import Q
from django.conf import settings
from django.core.management.base import BaseCommand

from film20.core.models import Film, Person, Poster

class Command( BaseCommand ):
    def handle( self, *args, **options ):
        films = Film.objects.filter( Q( hires_image__isnull=False) | Q( image__isnull=False ) )
        persons = Person.objects.filter( Q( hires_image__isnull=False, hires_image__gt='' ) | Q( image__isnull=False, image__gt='' ) )
        objects = list( films ) + list( persons )

        print "objects to migrate:", len( objects )

        for obj in objects:
            image = obj.hires_image or obj.image
            if image != '':
                p, c = Poster.objects.get_or_create( object=obj, image=image, LANG=None, defaults={ 'is_main': True } )

            else:
                pass
                #print obj.permalink
