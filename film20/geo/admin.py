import logging
logger = logging.getLogger(__name__)
try:
    from django.contrib.gis import admin
    from geo.models import TimeZone

    class TimeZoneAdmin(admin.OSMGeoAdmin):
        search_fields = ['tzid']

    admin.site.register(TimeZone, TimeZoneAdmin)
except Exception, e:
    pass

