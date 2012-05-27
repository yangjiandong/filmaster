#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from film20.recommendations.bot_helper import *

fetch_synopses_for_recently_imported_films(fetcher="enwikipedia")
fetch_synopses_for_recently_imported_films_no_synopsis(fetcher="rottentomatoes")
