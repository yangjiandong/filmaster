#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.bot_helper import *

#fetch_synopses_for_films() 
#fetch_synopses_for_films_no_localized_film(offset=0, number=5000)
fetch_synopses_for_films_no_synopses(offset=0, number=5000)

#fetch_synopses_for_recently_imported_films()
