from film20.import_films.tmdb import search, person_search, getMovieInfo, imdb
from film20.import_films.imdb_fetcher import save_poster
from film20.utils.texts import normalized_text

import logging
logger = logging.getLogger(__name__)


def match(film, result, fuzzy=False):
    prod_date = result['released'] or ''
    name = result['name'] or ''
    title_norm = normalized_text(name) or name
    
    if title_norm != film.title_normalized:
        return False
    
    if not prod_date or not film.release_year:
        return False
    try:
        year = int(prod_date.split('-')[0])
    except (IndexError, ValueError), e:
        return False
    
    years = (film.release_year, )
    if fuzzy:
        years += (film.release_year + 1, film.release_year - 1)
    return year in years
 

def fetch_film_by_title(filmaster_film):
    """
       Function takes Filmaster movie object,
       try to fetch movie object from tmdb and returns it
    """
    localized = filmaster_film.get_localized_film('en')
    titles = localized and localized.title and (localized.title, ) or ()
    if not filmaster_film.title in titles:
        titles += (filmaster_film.title, )
    for title in titles:
        if filmaster_film.release_year:
            results = search(title + " %s" % filmaster_film.release_year)
            for result in results:
                if match(filmaster_film, result):
                    return result
        
        results = search(title)
        for result in results:
            if match(filmaster_film, result):
                return result
        for result in results:
            if match(filmaster_film, result, fuzzy=True):
                return result
                
def fetch_person_by_name(filmaster_person):
    """
       Function takes Filmaster person object,
       try to fetch person object from tmdb and returns it
    """
    results = person_search(filmaster_person.__unicode__())
    if results:
        return results[0]
    else:
        return None

def fetch_film_by_id(filmaster_film):
    """
       Function takes Filmaster movie object,
       try to fetch movie object using imdb_code from filmaster movie
       and return tmdb movie object
    """
    try:
        film = imdb("tt"+filmaster_film.imdb_code)
        tmdb_film = getMovieInfo(film.getId())
        return tmdb_film
    except Exception, e:
        logger.exception(e)
        return False

def save_tmdb_poster(filmaster_object, tmdb_object):
    """
       Function takes Filmaster imdb object,
       tmdb object, try to download poster from tmdb and save it
    """
    if tmdb_object.get('images'):
        try:
            poster_url = tmdb_object['images'][0]['url']
        except KeyError, e:
            return False
        status = save_poster(filmaster_object, poster_url)
        return status
    else:
        return False



