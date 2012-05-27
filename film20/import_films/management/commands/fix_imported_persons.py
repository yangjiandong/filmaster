from imdb import IMDb
import re, htmlentitydefs

import logging
logger = logging.getLogger(__name__)

from optparse import make_option
from django.db.models import Q
from django.conf import settings

from film20.utils.texts import levenshtein
from film20.core.models import Film, Person, Character
from film20.core.management.base import BaseCommand
from film20.merging_tools.views import do_people_merging_resolve

def unescape( text ):
    def fixup( m ):
        text = m.group( 0 )
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x":
                    return unichr( int( text[3:-1], 16 ) )
                else:
                    return unichr( int( text[2:-1] ) )
            except ValueError:
                pass
        else:
            try:
                text = unichr( htmlentitydefs.name2codepoint[text[1:-1]] )
            except KeyError:
                pass
        return text
    return re.sub( "&#?\w+;", fixup, text )

def compare( a, b, distance=1 ):
    clean = lambda x: unescape( x.replace( ' - IMDb', '' ).replace( 'IMDb - ', '' ) )
    return levenshtein( clean( a ), clean( b ) ) <= distance

class PersonFixer( object ):
    def __init__( self, person, imdb=None, min_matched_movies=3 ):
        self.person = person
        self.imdb = imdb or IMDb()
        self.min_matched_movies = min_matched_movies

    def fix( self ):
        # skip if already verified or merged
        try:
            self.person = Person.objects.get( pk=self.person.pk )
            if self.person.verified_imdb_code:
                logger.info( "Person imdb code already verified, skipping" )
                return True
        except Person.DoesNotExist:
            logger.info( "Person already merged, skipping" )
            return True

        full_name = self.full_name
        short = self.is_short_imdb_code
        imdb_code = self.full_imdb_code

        logger.info( "Person: %s (%s)" % ( self.person, imdb_code ) )
        
        # 1. check assigned imdb code
        if self.person.imdb_code:
            logger.info( "1. checking by imdb code" )

            # 1.1. if code is short try find person by long imdb code
            if short:
                logger.info( "1.1. imdb code is short, trying to find a person by long code: %s" % imdb_code )
                try:
                    person_lcm = Person.objects.get( imdb_code=imdb_code )
                except Person.DoesNotExist:
                    logger.info( " -- Person with long imdb_code does not exists" )
                    person_lcm = None

            imdb_person = self.imdb.get_person( imdb_code )
            self.imdb.update( imdb_person )
            if imdb_person:
                logger.info( "Found imdb person: %s(%s)" % ( imdb_person, imdb_person.personID ) )
                if compare( full_name, imdb_person['name'] ):
                    logger.info( " -- Name match !" )
                    if short and person_lcm:
                        logger.info( "code is short and person with full imdb_code exists %s %s" % ( person_lcm.name, person_lcm.surname ) )
                        if person_lcm.verified_imdb_code or compare( full_name, "%s %s" % ( person_lcm.name, person_lcm.surname ), 3 ):
                            if person_lcm.permalink.endswith( '-1' ) or '&#' in person_lcm.name + person_lcm.surname:
                                keep = 'self'
                            else:
                                keep = person_lcm
                            logger.info( " merging %s(%s)[%s] -- %s" % ( person_lcm, person_lcm.imdb_code, person_lcm.permalink, 'to delete' if keep == 'self' else 'to keep' ) )
                            self.merge_with( person_lcm, keep, imdb_code )
                    else:
                        logger.info( "  -- setting imdb_code to verified !" )
                        self.set_imdb_code_verified( imdb_code )
                    
                    return True

                logger.info( "  -- Name not match ..." )
        
        # 2. find by name
        logger.info( "2. searching by name ..." )
        try:
            results = self.imdb.search_person( full_name )
        except Exception, e:
            results = []
            logger.error( 'Imdb error: %s' % e )

        best_match = []
        for item in results:
            if compare( item['name'], full_name, 1 ):
                self.imdb.update( item )
                best_match.append( item )

        if len( best_match ) == 0:
            logger.error( "  --  cannot find any person ..." )
            return False

        # 3. compare movies directors, writters and actors
        logger.info( "3. comparing movies directing, acting" )
        
        if self.person.is_director:
            movies_directed = self.movies_directed
            logger.info( " - person is director" )
            logger.info( "    directed: %s" % movies_directed )
        else:
            movies_directed = []

        if self.person.is_writer:
            movies_written = self.movies_written
            logger.info( " - person is writer" )
            logger.info( "    written: %s" % movies_written )
        else:
            movies_written = []

        if self.person.is_actor:
            movies_acted = self.movies_acted
            logger.info( " - person is actor" )
            logger.info( "    acted: %s" % movies_acted )
        else:
            movies_acted = []
        
        all_movies_len = len( movies_directed ) + len( self.movies_written ) + len( movies_acted )

        if all_movies_len > 0:
            not_matches_movies = {}
            for item in best_match:
                not_matches_movies[item] = []
                imdb_movies_acted = [ m.movieID for m in item.get( 'actor', [] ) + item.get( 'actress', [] ) + item.get( 'self', [] ) ]
                imdb_movies_written = [ m.movieID for m in item.get( 'writer' ) or [] ]
                imdb_movies_directed = [ m.movieID for m in item.get( 'director' ) or [] ]

                logger.info( "   - comparing movies for searched item: %s(%s)" % ( item, item.personID ) )
                # director
                for f in movies_directed:
                    if f not in imdb_movies_directed:
                        not_matches_movies[item].append( f )

                # writer
                for f in movies_written:
                    if f not in imdb_movies_written:
                        not_matches_movies[item].append( f )

                # writer
                for f in movies_acted:
                    if f not in imdb_movies_acted:
                        not_matches_movies[item].append( f )

            not_matches_movies = sorted( not_matches_movies.iteritems(), key=lambda ( k,v ): ( len( v ) , k ) )
            first_person, movies = not_matches_movies[0]
            if len( movies ):
                logger.info( " -- not matched movies: %s" % movies )
                self.add_comment( 'not matched movies: %s' % ', '.join( movies ) )
            
                matched_movies_len = all_movies_len - len( movies )
                if matched_movies_len < self.min_matched_movies:
                    logger.info( " -- matched movies: %d, min. matched movies: %d [SKIPPING]" % ( matched_movies_len, self.min_matched_movies ) )
                    return False
                logger.info( " -- matched movies: %d, min. matched movies: %d [OK]" % ( matched_movies_len, self.min_matched_movies ) )

            else:
                logger.info( "  - all movies matches, imdb code: %s verified" % imdb_code )

            imdb_code = first_person.personID
            try:
                to_merge = Person.objects.get( imdb_code=imdb_code )
                logger.info( "  - Person with same imdb_code already exists ..." )
                if to_merge.verified_imdb_code:
                    logger.info( "    imdb code is verified [MERGING]" )
                    if to_merge.permalink.endswith( '-1' ) or '&#' in to_merge.name + to_merge.surname:
                        keep = 'self'
                    else:
                        keep = to_merge
                    logger.info( "      merging %s(%s)[%s] -- %s" % ( to_merge, to_merge.imdb_code, to_merge.permalink, 'to delete' if keep == 'self' else 'to keep' ) )
                    self.merge_with( to_merge, keep, imdb_code )

                else:
                    print "   and imdb code is not verified [SKIPPING]"
                    self.add_comment( 'probable imdb_code: %s' % imdb_code )

            except Person.DoesNotExist:
                logger.info( "  - Person with same imdb_code does not exist, code verified !" )
                self.set_imdb_code_verified( imdb_code )

    @property
    def is_verified( self ):
        return self.person.verified_imdb_code

    @property
    def is_short_imdb_code( self ):
        return self.person.imdb_code is not None and len( self.person.imdb_code ) < 7

    @property
    def full_name( self ):
        return "%s %s" % ( self.person.name, self.person.surname )

    @property
    def full_imdb_code( self ):
        if self.person.imdb_code:
            length = len( self.person.imdb_code )
            if length == 7:
                return self.person.imdb_code
            return '0' * ( 7 - length ) + self.person.imdb_code
        return None
    
    @property
    def movies_acted( self ):
        return [ f.imdb_code for f in Film.objects.filter( character__person=self.person, imdb_code__isnull=False ).distinct() ]

    @property
    def movies_directed( self ):
        return [ f.imdb_code for f in Film.objects.filter( directors=self.person, imdb_code__isnull=False ).distinct() ]

    @property
    def movies_written( self ):
        return [ f.imdb_code for f in Film.objects.filter( writers=self.person, imdb_code__isnull=False ).distinct() ]

    def merge_with( self, to_merge, keep='self', imdb_code=None ):
        try:
            if keep == 'self':
                to_keep = self.person
                to_delete = to_merge
            else:
                to_keep = to_merge
                to_delete = self.person

            imdb_code = imdb_code or to_keep.imdb_code
            do_people_merging_resolve( to_keep, to_delete )

            self.person = to_keep
            self.set_imdb_code_verified( imdb_code )
        except Exception, e:
            logger.error( 'Upps cannot merge: %s' % e )
            self.add_comment( 'cannot merge: %s' % e )

    def set_imdb_code_verified( self, imdb_code ):
        self.person.imdb_code = imdb_code
        self.person.verified_imdb_code = True
        self.person.save()

    def add_comment( self, comment ):
        if self.person.import_comment and self.person.import_comment != comment:
            comment = "%s, %s" % ( self.person.import_comment, comment )
        self.person.import_comment = comment
        self.person.save()


MIN_MATCHED_MOVIES = getattr( settings, "MIN_MATCHED_MOVIES", 3 )

class Command( BaseCommand ):
    option_list = BaseCommand.option_list + (
        make_option( '--limit', dest='limit', default=0, type='int' ),
        make_option( '--reported-duplicates', dest='reported', default=False, action='store_true' ),
        make_option( '--mmm', dest='min_matched_movies', default=MIN_MATCHED_MOVIES, type='int' ),
    )

    def handle( self, *args, **opts ):
        self.opts = opts

        imdb = IMDb()

        limit = self.opts.get( 'limit' )
        reported =  opts.get( 'reported' )
        min_matched_movies = self.opts.get( 'min_matched_movies' )
        
        persons = Person.objects.filter( verified_imdb_code=False )
        if reported:
            persons = persons.filter( Q( duplicate_person_a__isnull=False ) | Q( duplicate_person_b__isnull=False ) )

        persons = persons.extra(
            select = { 'popularity': 'actor_popularity + director_popularity + writer_popularity' },
            order_by = ( "-popularity", )
        )        
        if limit > 0:
            persons = persons[:limit]
 
        print ":: Persons to check: %d, MIN_MATCHED_MOVIES: %d" % ( persons.count(), min_matched_movies )

        for person in persons:
            fixer = PersonFixer( person, imdb, min_matched_movies )
            fixer.fix()

        print ":: Persons with not verified imdb codes: %d" % Person.objects.filter( verified_imdb_code=False ).count()
