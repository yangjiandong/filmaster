import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from settings import *
import os.path
from film20.core.models import *

def find_missing_posters():
    for f in Film.objects.exclude(image=""):
        if os.path.isfile(f.image.path):
            pass
        else:
            f.image = ""
            f.save()

find_missing_posters()