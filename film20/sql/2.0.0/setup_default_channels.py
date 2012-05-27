import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'film20.settings'
import sys
sys.path.insert(0, os.path.abspath('..'))
print sys.path[0]

# mark some channels as default using admin before runing this script !!!
from film20.core.models import Profile

query = Profile.objects.filter(country__isnull=False)
total = query.count()

for i,p in enumerate(query):
    print "%s / %s" % (i+1, total)
    p.no_cinema_update = True
    p.set_default_channels()
