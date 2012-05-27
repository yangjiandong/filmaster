#!/usr/bin/python
from cgi import parse_qs
import json
import re
import logging
logger = logging.getLogger(__name__)

#from django.contrib.gis.utils.geoip import GeoIP
from django.conf import settings

from film20.utils import cache

from .utils import get_country_and_tz_by_lat_lng

class LazyGeo(object):
    @classmethod
    def set_country_and_tz_by_lat_lng(cls, request, geo):
        if not 'latitude' in geo or not 'longitude' in geo:
            return False
        lat, lng = geo['latitude'], geo['longitude']
        ret = get_country_and_tz_by_lat_lng(lat, lng)
        if ret:
            geo['country_code'], geo['timezone'] = ret
            return True
        return False

    def __get__(self, request, obj_type=None):
        from film20.geo.models import BaseTimeZone
        geo = getattr(request, '_geo', None) or {}
        if geo:
            return geo

        assert request.user, "authentication middleware is required"

        logger.debug("cookies: %r", request.COOKIES)
        html5geo = request.COOKIES.get('geolocation')
        if html5geo is not None:
            try:
                html5geo = html5geo and json.loads(parse_qs('geolocation='+html5geo)['geolocation'][0])
                for param in ('latitude', 'longitude', 'accuracy'):
                    geo[param] = html5geo['coords'][param]
                    geo['source'] = 'html5'
            except (IndexError, ValueError, TypeError), e:
                logger.warning("html5 geolocation cookie decode error: %s", unicode(e))
                geo = {}

        if not geo:
            try:
                #gi = GeoIP()
                ip = settings.FAKE_IP or request.META['REMOTE_ADDR']
                #data = gi.city(ip)
                data = None
                if data and 'latitude' in data and 'longitude' in data:
                    geo.update(data)
                    geo['accuracy'] = 100000
                    geo['source'] = 'geoip'
            except Exception, e:
                logger.exception(e)

        # trying to determine country_code and timezone may be expensive,
        # so we are caching this info
        accuracy = geo.get('accuracy')
        if accuracy:
            key = cache.Key("geolocation", request.user.is_authenticated() and request.user.id or request.session.session_key)
            cached_geo = cache.get(key)
            if cached_geo is not None and cached_geo.get('accuracy') <= accuracy * 2:
                geo = cached_geo
            else:
                if self.set_country_and_tz_by_lat_lng(request, geo):
                    cache.set(key, geo)

        if not 'country_code' in geo:
            langs = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            langs = [l.strip() for l in langs.split(',')]
            if langs:
                match = re.match("(\w\w)(-(\w\w))?", langs[0])
                if match:
                    lang, _, code = match.groups()
                    country_code = (code or lang).upper()
                    timezone = BaseTimeZone.tzid_for_country(country_code)
                    if timezone:
                        geo['country_code'] = country_code
                        geo['timezone'] = timezone
                        geo['source'] = 'accept_language'

        if not 'country_code' in geo:
            geo['country_code'] = settings.COUNTRY_CODE
            geo['timezone'] = BaseTimeZone.tzid_for_country(settings.COUNTRY_CODE)
            geo['source'] = 'settings'

        request._geo = geo
        return geo

    @classmethod
    def profile_post_save(cls, sender, instance, created, *args, **kw):
        if instance.is_field_changed('country'):
            cache.delete(cache.Key("geolocation", instance.user_id))

import pytz
class LazyTimezone(object):
    def __get__(self, request, obj_type=None):
        assert request.user, "authentication middleware is required"
        timezone_id = request.REQUEST.get('timezone', None)
        if not timezone_id:
            timezone_id = request.user.is_authenticated() and request.user.get_profile().timezone_id
        if not timezone_id:
            timezone_id = request.geo.get('timezone')

        try:
            timezone = timezone_id and pytz.timezone(timezone_id) or pytz.utc
        except pytz.UnknownTimeZoneError:
            logger.warning("Unknown timezone %s, using UTC", timezone_id)
            timezone = pytz.utc
        return timezone

class GeoMiddleware(object):
    """
    Handle geolocation detection, using geoip, html5, Accept-Language header
        or default settings
    """
    def process_request(self, request):
       request.__class__.geo = LazyGeo()
       request.__class__.timezone = LazyTimezone()

