from imdb import IMDb

import logging
logger = logging.getLogger(__name__)

from optparse import make_option
from django.db.models import Q
from django.conf import settings

from film20.core.models import Film
from film20.core.management.base import BaseCommand
from film20.import_films.imdb_fetcher import get_runtime

class Command( BaseCommand ):
    option_list = BaseCommand.option_list + (
        make_option( '--limit', dest='limit', default=0, type='int' ),
    )

    def handle( self, *args, **opts ):

        limit = opts.get( 'limit' )
        
        films = Film.objects.filter( verified_imdb_code=True, length=None ).order_by( '-popularity' ) 
        if limit > 0:
            films = films[:limit]
        
        imdb = IMDb()
        print ":: Films to update: %d" % films.count()

        for film in films:
            print " --", film
            movie = imdb.get_movie( film.imdb_code )
            if movie:
                runtime = get_runtime( movie )
                if runtime:
                    print "   `--", runtime, "min"
                    film.length = runtime
                    film.save()

