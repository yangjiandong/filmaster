from imdb import IMDb
import unicodedata
import re, htmlentitydefs

import logging
logger = logging.getLogger(__name__)

from optparse import make_option
from django.db.models import Q
from django.conf import settings

from film20.utils.texts import levenshtein
from film20.core.models import Film, Person, Character
from film20.core.management.base import BaseCommand
from film20.import_films.management.commands.fix_imported_persons import unescape, compare

class FilmFixer( object ):

    IMDB_MOVIE_TYPES = (
        'tv',
        'movie',
        'tv movie',
        'video movie',
        'tv mini series',
        'tv mini-series',
    )

    def __init__( self, film, imdb=None ):
        self.film = film
        self.imdb = imdb or IMDb()

    def fix( self ):

        print self.film

        # skip if already verified or dont exists
        try:
            self.film = Film.objects.get( pk=self.film.pk )
            if self.film.verified_imdb_code:
                logger.info( "Film imdb code already verified, skipping" )
                return True
        except Film.DoesNotExist:
            logger.info( "Film does not exist, skipping" )
            return True

        matched = self.__search_movie( self.film.title )
        if not len( matched ):
            title_normalized = unicodedata.normalize( 'NFKD', self.film.title ).encode( 'ascii', 'ignore' )
            if self.film.title != title_normalized:
                matched = self.__search_movie( title_normalized )

        if len( matched ) == 1:
            self.__set_imdb_code_verified( matched[0].movieID )

        elif len( matched ) > 1:
            self.__add_comment( "too many matching movies: '%s'" % ','.join( [ m.movieID for m in matched ] ) )

        else:
            self.__add_comment( "nothing matches" )

    def __compare_film( self, movie ):
        if movie.has_key( 'kind' ) and movie.has_key( 'year' ) and movie['kind'] in self.IMDB_MOVIE_TYPES and self.film.release_year == movie['year']:
            if compare( self.film.title, movie['title'], 0 ):
                return True
            
            for aka in movie.get( 'akas', [] ):
                if compare( self.film.title, aka ):
                    return True
        return False

    def __search_movie( self, title ):
        print " --- searching for:", title
        results = self.imdb.search_movie( title )
        return filter( self.__compare_film, results )

    def __set_imdb_code_verified( self, imdb_code ):
        print " -- setting %s, code %s verified" % ( self.film, imdb_code )
        films = Film.objects.filter( imdb_code=imdb_code ).exclude( pk=self.film.pk )
        if len( films ):
            if len( films ) > 1:
                return self.__add_comment( "imdb code '%s' already assigned to other films" % imdb_code )
            
            elif films[0].verified_imdb_code:
                return self.__add_comment( "imdb code '%s' already assigned to: '%s'" % ( imdb_code, films[0].pk ) )

            else:
                films[0].imdb_code = None
                films[0].save()

        self.film.imdb_code = imdb_code
        self.film.verified_imdb_code = True
        self.film.save()

    def __add_comment( self, comment ):
        print " --- adding %s comment: %s" % ( self.film, comment )
        if self.film.import_comment and self.film.import_comment != comment:
            comment = "%s, %s" % ( self.film.import_comment, comment )
        self.film.import_comment = comment
        self.film.save()


class Command( BaseCommand ):
    option_list = BaseCommand.option_list + (
        make_option( '--limit', dest='limit', default=0, type='int' ),
        make_option( '--skip-previously-not-matched', dest='skip_not_matched', default=False, action='store_true' ),
    )

    def handle( self, *args, **opts ):
        self.opts = opts

        imdb = IMDb()

        limit = self.opts.get( 'limit' )
        not_matches_movies = opts.get( 'skip_not_matched' )
        
        films = Film.objects.filter( verified_imdb_code=False )
        if not_matches_movies:
            films = films.filter( import_comment__isnull=True )

        films = films.order_by( '-popularity' ) 

        if limit > 0:
            films = films[:limit]
        
 
        print ":: Films to check: %d" % films.count()

        for film in films:
            fixer = FilmFixer( film, imdb )
            fixer.fix()

        print ":: Films with not verified imdb codes: %d" % Film.objects.filter( verified_imdb_code=False ).count()
