# -*- coding: utf-8 -*-

import imdb_fetcher

from django.db import transaction

from film20.core.models import *

def update_imdb_code(film):
    movie = imdb_fetcher.get_movie_by_title_and_year(film.title, film.release_year)
    if not movie:
        print "WARN: couldn't find film %s (%s) in imdb" % (film.title, film.release_year)
    elif movie.getID()!=film.imdb_code:
        film.imdb_code=movie.getID()
        film.save()

@transaction.commit_manually
def update_imdb_codes_for_films(qs):
    updated = 0

    for film in qs:
        try:
            movie = imdb_fetcher.get_movie_by_title_and_year( film.title, film.release_year )
            if movie:
                film.imdb_code = movie.getID()
                film.verified_imdb_code = True
                film.save()
                
                updated += 1
            else:
                print "WARN: couldn't find film #%i in imdb" % film.id

            if updated % 100 == 0:
                transaction.commit()
        except Exception, e:
            print "ERROR: failed to fetch/process #%i" % film.id
            print e
            #transaction.rollback()
    transaction.commit()

def update_short_imdb_codes():
    qs = Film.objects.extra(where=['length(imdb_code)=5'])
    update_imdb_codes_for_films(qs)
    
def update_valid_imdb_codes():
    qs = Film.objects.extra(where=['length(imdb_code)=7'])
    update_imdb_codes_for_films(qs)
    
def update_null_imdb_codes():
    qs = Film.objects.filter(imdb_code__isnull)
    update_imdb_codes_for_films(qs)
    
def update_all_imdb_codes():
    qs = Film.objects.all()
    update_imdb_codes_for_films(qs)
    
def update_not_verified_codes():
    qs = Film.objects.filter(verified_imdb_code=False)
    update_imdb_codes_for_films(qs)
    
def elapsed_time(start):
    import time
    t = int(time.time()-start)
    dur = 1
    elapsed = []
    for v in [60,60,24]:        
        elapsed.append(t % v)
        t = t/v
    elapsed.append(t)
    return elapsed
    
def run(fun):
    import time
    
    start = time.time()
    print "started at %s" % time.ctime()
    fun()
    elapsed = elapsed_time(start)
    print "finished at %s, in %i days, %i hours, %i minutes, %i seconds" \
        % (time.ctime(), elapsed[3], elapsed[2], elapsed[1], elapsed[0])


    
def main():            
    run(update_not_verified_codes)
if __name__=="__main__":
    main()
