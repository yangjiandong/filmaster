#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

from django.conf import settings

from film20.core.models import Film
from film20.utils import cache_helper as cache
from film20.utils.slughifi import slughifi

def is_good_film_permalink( permalink ):
    try:
        Film.objects.get( permalink=permalink )
        return False
    except Film.DoesNotExist:
        return True

def get_film_permalink( film, attempts=100 ):    
    permalink = slughifi( film.title )
    if is_good_film_permalink( permalink ):
        return permalink

    root_permalink = "%s-%s" % ( permalink, film.release_year )
    if is_good_film_permalink( root_permalink ):
        return root_permalink
    
    for i in range( 1, attempts ):
        permalink = "%s-%s" % ( root_permalink, i )
        if is_good_film_permalink( permalink ):
            return permalink

    return None # O_O

def get_other_languages( ):
    if settings.LANGUAGE_CODE == 'en':
        return [ 'pl' ]
    else: return ['en']

def clear_actors_cache( film ):
    from film20.core.film_views import MAX_ACTORS

    cache.delete_cache( cache.CACHE_FILM_ACTORS, "%s_%s_%s" % ( film.permalink, 0, MAX_ACTORS ) )
    cache.delete_cache( cache.CACHE_FILM_ACTORS, "%s_%s_%s" % ( film.permalink, MAX_ACTORS, 100 ) )

    cache.delete( cache.Key( 'film_actors', film ) )

def clear_directors_cache( film ):
    cache.delete( cache.Key( 'film_directors', film ) )
 
