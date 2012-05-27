import os, sys
PROJECT_ROOT = os.curdir
#sys.path.insert(0, os.path.join(PROJECT_ROOT+"/", "fetcher"))

os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
from datetime import datetime
from film20.import_ratings.import_ratings_helper import import_ratings

import_ratings()
