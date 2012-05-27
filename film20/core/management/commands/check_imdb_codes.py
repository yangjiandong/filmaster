# Django
from django.core.management.base import BaseCommand, CommandError

# Project
from film20.import_films.imdb_fetcher import get_movie_by_id, get_movie_by_title_and_year
from film20.core.models import Film

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    
    def get_films(self):
        logger.info("Get all films")
        return Film.objects.all().order_by('imdb_code')

    def not_verified(self, film):
        logger.info("Film %s not verified" % film)
        film.verified_imdb_code = False
        film.save()
        return True
    
    def verified(self, film):
        logger.info("Film %s verified" % film)
        film.verified_imdb_code = True
        film.save()
        return True
    
    def match_title(self, movie_log):
        logger.info("Try to match title: %s" % movie_log['film_title'])
        if movie_log['imdb_title'] == movie_log['film_title']:
            return True
        return False
    
    def match_year(self, movie_log):
        logger.info("Try to match year: %s (%s)" % (movie_log['film_title'], movie_log['film_year']))
        if movie_log['imdb_year'] == movie_log['film_year']:
            return True
        return False

    def match_alt_titles(self, movie_log):
        logger.info("Try to match alt titles %s" % movie_log['imdb_akas'])        
        if movie_log['imdb_akas']:
            for aka in movie_log['imdb_akas']:
               title = aka.split('::')[0]
               if title == movie_log['film_title']:
                   logger.info("Alternative title %s for %s" % (title, movie_log['film_title']))
                   return True
        return False

    def get_film_from_imdb(self, film):
        logger.info("Get movie %s by IMDB id %s" % (film, film.imdb_code))
        movie = get_movie_by_id(film.imdb_code, "http")
        try:
            imdb_year = movie.get('year')
        except:
            imdb_year = None
        try: 
            imdb_title = movie.get('title')
        except:
            imdb_title = None
        try:
            imdb_akas = movie.get('akas')
        except:
            imdb_akas = None
            
        movie_log = {"film":film, "film_id":film.id, "film_title":film.title, "film_year":film.release_year, 
                     "imdb_code":film.imdb_code, "imdb_title":imdb_title, "imdb_akas":imdb_akas, "imdb_year":imdb_year}
        return movie_log

    def verify_imdb_code(self, film, none, alt):
        if not film.imdb_code:
            logger.warning("Film %s doesn't have IMDB code" % film)
            movie = self.not_verified(film)
            none.append(movie)
            return False
        else:
            movie_log = self.get_film_from_imdb(film)
            if self.match_title(movie_log):
                if self.match_year(movie_log):
                    self.verified(movie_log['film'])
                    return True
                else:
                    logger.warning("Wrong year: %s (%s) != %s" % (movie_log['film_title'], movie_log['film_year'], movie_log['imdb_year']))
                    self.not_verified(movie_log['film'])
                    none.append(movie_log)
                    return False
            else:
                if self.match_alt_titles(movie_log):
                    if self.match_year(movie_log):
                        self.verified(movie_log['film'])
                        alt.append(movie_log)
                        return True
                    else:
                        self.not_verified(movie_log['film'])
                        none.append(movie_log)
                else:
                    self.not_verified(movie_log['film'])
                    none.append(movie_log)
                return False

    def handle(self, *args, **opts):
        films = self.get_films()
        alt = []
        none = []
        
        for film in films:
            try:
                self.verify_imdb_code(film, none, alt)
            except:
                logger.exception
        print "---------- ALT -------------"
        print len(alt)
        print alt
        print "---------- NONE -------------"
        print len(none)
        print none
