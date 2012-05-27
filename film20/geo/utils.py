#!/usr/bin/python
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from film20.utils import cache

def _get_country_and_tz_by_lat_lng(lat, lng):
    try:
        from film20.geo.models import TimeZone
        tz = TimeZone.objects.get(geom__contains="POINT(%s %s)" % (lng, lat))
        logger.debug("gis: country_code: %s, timezone: %s", tz.country_code, tz.tzid)
        return tz.country_code, tz.tzid
    except Exception, e:
        logger.debug(unicode(e))

    if not settings.SKIP_EXTERNAL_REQUESTS:
        try:
            from geonames import timezone
            data = timezone(lat, lng)
            logger.debug("geonames: country_code: %s, timezone: %s", data['countryCode'], data['timezoneId'])
            return data['countryCode'], data['timezoneId']
        except Exception, e:
            logger.warning(unicode(e))

    logger.warning('no timezone and country code for (%s %s)', lat, lng)
    return False

def get_country_and_tz_by_lat_lng(lat, lng):
    key = cache.Key('country_tz', lat, lng)
    data = cache.get(key)
    if data is None:
        data = _get_country_and_tz_by_lat_lng(lat, lng)
        cache.set(key, data)
    return data

