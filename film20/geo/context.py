#!/usr/bin/python
from django.conf import settings

def geo_context(request):
        try:
                city = request.city
                region = request.region
        except:
                city = False
                region = False
        return {'geo_city': city, 'geo_region': region}