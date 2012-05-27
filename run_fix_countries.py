import os, sys
PROJECT_ROOT = os.curdir
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from film20.import_films.update_countries import update_all_films

update_all_films()

