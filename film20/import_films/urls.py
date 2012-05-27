from django.conf.urls.defaults import *

from film20.config.urls import *
from film20.import_films.views import import_film
from film20.import_films.feeds import import_film_rss

importfilmspatterns = patterns('',
    url(r'^'+urls["ADD_FILMS"]+'/$', import_film, name='import_film'),
    url(r'^'+urls["ADD_FILMS"]+'/rss/$', import_film_rss),
)
