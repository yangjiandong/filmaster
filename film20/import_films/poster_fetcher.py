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
from django.template import defaultfilters
import slughifi
import os, sys, getopt, glob
from settings import *
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings' 
import imdb
from film20.core.models import *
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from film20.tagging.models import Tag
import urllib2
from django.core.files import File
try:
    from PIL import Image
except ImportError:
    import Image

import logging
logger = logging.getLogger(__name__)

def save_name_surname(name_surname):
    PREFIXES = {
        'ab':'ab',
        'Ab':'Ab',
        'abu':'abu',
        'Abu':'Abu',
        'bin':'bin',
        'Bin':'Bin',
        'bint':'bint',
        'Bint':'Bint',
        'da':'da',
        'Da':'Da',
        'de':'de',
        'De':'De',
        'degli':'degli',
        'Degli':'Degli',
        'della':'della',
        'Della':'Della',
        'der':'der',        
        'Der':'Der',
        'di':'di',
        'Di':'Di',
        'del':'del',
        'Del':'Del',
        'dos':'dos',
        'Dos':'Dos',
        'du':'du',
        'Du':'Du',
        'el':'el',
        'El':'El',
        'fitz':'fitz',
        'Fitz':'Fitz',
        'haj':'haj',
        'Haj':'Haj',
        'hadj':'hadj',
        'Hadj':'Hadj',
        'hajj':'hajj',
        'Hajj':'Hajj',
        'ibn':'ibn',
        'Ibn':'Ibn',
        'ter':'ter',
        'Ter':'Ter',
        'tre':'tre',
        'Tre':'Tre',
        'van':'van',
        'Van':'Van',
        'Von':'Von',
        'von':'von',
        }
    
    list = name_surname.split(' ')
    if len(list)> 2:
        for index, element in enumerate(list):
            if PREFIXES.has_key(element):
                name = " ".join(list[:index])
                surname = " ".join(list[index:])
                return [name, surname]
            elif list[-1] == "Jr.":
                name = " ".join(list[:-2])
                surname = " ".join(list[-2:])
                return [name, surname]
            else:    
                name = list[0]
                surname = " ".join(list[1:])
                return [name, surname]
    elif len(list) ==  2:
        name = list[0]
        surname = list[1]
        return [name, surname]
    else:
        name = list[0]
        surname = list[0]
        return [name, surname]

def fetch_poster(url):

    try: 
        htmlSource=urllib2.urlopen(url)
        poster = htmlSource.read()
        htmlSource.close()
    except URLError, e:
        pass
   
    
    
    tmpfile = open("tmp.jpg", "wb")
    tmpfile.write(poster)
    tmpfile.close

def resize_image():
    im1 = Image.open("tmp.jpg")
    im2 = im1.resize((71, 102), Image.ANTIALIAS)
    im2.save("tmp.jpg")
    
def save_poster(film, url):
    fetch_poster(url)
    resize_image()
    logger.debug("Saving Poster. ID=" + unicode(film))
    filename = str(film.permalink) + ".jpg"
    #filename = "1.jpg"
    if len(filename) > 80:
        filename = filename[:80]
    ia = len(filename)
    filenamelenght = str(ia)
    logger.debug("Saving Poster. ID=" + " " + filenamelenght + " " + unicode(film)) 
    f = open('tmp.jpg', 'rb')
    myfile = File(f)
    film.image.save(filename, myfile)
    
    
def save_writers(film, writers):
    for writer in writers:
        name_surname = writer.get('name')
        writer_link = slughifi.slughifi(name_surname)
        writer_imdb = writer.personID
        writer_name, writer_surname = save_name_surname(name_surname)
        dbdir = Person.objects.filter(permalink = writer_link)
        if dbdir.count() == 0:
            person = Person(name = writer_name, surname = writer_surname, is_writer = True, status = 1, version = 1, type=2, permalink = writer_link, imdb_code =writer_imdb, actor_popularity=0,director_popularity=0,actor_popularity_month=0,director_popularity_month=0,writer_popularity=0,writer_popularity_month=0,)
            person.save(saved_by=2)
            film.writers.add(person)
            logger.debug("Saving Writer. ID=" + unicode(person))
        else:
            person = dbdir[0]
            person.is_writer = True                    
            person.save(saved_by=2)
            film.writers.add(person)
            logger.debug("Saving Writer. ID=" + unicode(person))

def save_countries(film, countries):
    countries_list = ""
    for country in countries:
        country_list = Country.objects.filter(country=country)
        if country_list.count() == 0:
            coun = Country(country=country)
            coun.save()
            countries_list = country + "," + countries_list
            film.production_country.add(coun)
            logger.debug("Saving Country. ID=" + unicode(coun)) 
        else:
            coun = country_list[0]
            countries_list = country + "," + countries_list
            film.production_country.add(coun)
            logger.debug("Saving Country. ID=" + unicode(coun))    
    film.production_country_list = countries_list
    film.save()
    logger.debug("Saving CountryList. ID=" + unicode(countries_list))

def main():
    a = imdb.IMDb('httpThin')
    films = Film.objects.all().order_by("-popularity")
    for film in films:
        mlist = a.search_movie(film.title)
        if len(mlist) > 0:
            movie = mlist[0]
            if film.title==movie.get('title'):
                film.imdb_code = movie.movieID
                a.update(movie, 'main')
                url = movie.get('cover url')
                if url:
                    save_poster(film, url)
                writers = movie.get('writer')
                if writers:
                    save_writers(film, writers)
                countries = movie.get('countries')
                if countries:
                    save_countries(film, countries)
    
    logger.debug("All posters fetched!") 
if __name__ == "__main__":
    main()
