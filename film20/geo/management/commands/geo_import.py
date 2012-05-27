from django.contrib.gis.utils import LayerMapping
from django.conf import settings
from django.db.models import Q

from film20.core.management.base import BaseCommand
from film20.geo.models import TimeZone, timezone_mapping

import os
import json

class Command(BaseCommand):
    def handle(self, *args, **kw):
        base_dir = os.path.join(os.path.dirname(__file__), '..', '..')
        shp_file = os.path.join(base_dir, 'world/tz_world_mp.shp')
        if not os.path.exists(shp_file):
            print "download http://efele.net/maps/tz/world/tz_world_mp.zip and unzip in film20/geo dir"
            print "also, due to some bug in gis code, set 'geo' database as default when this script is running"
            return
        lm=LayerMapping(
            TimeZone,
            'geo/world/tz_world_mp.shp', 
            timezone_mapping,
        )
        lm.save(verbose=True)

