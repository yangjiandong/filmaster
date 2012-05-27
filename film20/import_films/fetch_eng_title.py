#-*- coding: utf-8 -*-
import os, sys, getopt, glob
from settings import *
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings' 
from film20.core.models import *
import imdb
from imdb import IMDb, IMDbError
import slughifi
import re
import logging
logger = logging.getLogger(__name__)

def needle_in_haystack(needle, haystack): 
    reneedle = re.compile(needle)
    return needle in haystack

def save_countries(countries, film, title):
    for country in countries:
        
        if needle_in_haystack("USA", country) or needle_in_haystack("English", country):
            if not needle_in_haystack("working title", country):
                list = country.split("::")
                title = list[0]
                if len(title) > 128:
                    title = title[0:127]
                film.save_localized_title(title, "en", saved_by=2)
                logger.debug(unicode(country) +" imdbpy movie title: "+ unicode(title) +" filmaster - movie title: "+ unicode(film.permalink))         

def fetch_eng_title():
    count = 0
    for f in Film.objects.all().exclude(filmlocalized__LANG="en").order_by("-popularity"):
        a = imdb.IMDb()
        mlist = a.search_movie(f.title)
        if len(mlist) > 0:
            for m in mlist:
                if m.get('title') == f.title and m.get('year') == str(f.release_year):
                    try:
                        a.update(m, 'main')
                    except IMDbError, err:
                        continue
                    akas = m.get('akas')
                    if akas:
                        save_countries(akas,f,m.get('title'))
                        count = count + 1
    logger.debug("zrobione! zapisano tytuly dla " + str(count) +" filmow")

fetch_eng_title()
