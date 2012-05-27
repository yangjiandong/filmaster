#!/usr/bin/env python
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from film20.core.management.base import BaseCommand
from film20.recommendations.bot_helper import do_update_films_popularity
 
do_update_films_popularity()
