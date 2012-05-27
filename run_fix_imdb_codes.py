import os, sys
PROJECT_ROOT = os.curdir
#sys.path.insert(0, os.path.join(PROJECT_ROOT+"/", "fetcher"))
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'

from film20.import_films.update_imdb_codes import update_not_verified_codes

update_not_verified_codes()

