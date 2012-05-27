from django.conf import settings as _settings
from film20.config import messages as _messages
import datetime
import logging
logger = logging.getLogger(__name__)

def settings(request):
    return {'settings':_settings}

def msg(request):
    return {'msg':_messages}

def auth(request):
    from film20.account.models import OAUTH_SERVICES
    from django.contrib.auth import BACKEND_SESSION_KEY
    backend = request.session.get(BACKEND_SESSION_KEY)
    return {
        'OAUTH_SERVICES': OAUTH_SERVICES,
        'auth_backend':backend,
        'fc':backend and 'Facebook' in backend,
    }

class BaseContext(object):
    def __init__(self, request):
        self.request = request

class GlobalContext(BaseContext):
    @property
    def top_tags(self):
        from film20.core.models import Film
        return Film.get_top_tags()

    @property
    def js_data(self):
        geo = self.request.geo
        country_code = geo.get('country_code')
        main_city = _settings.COUNTRY_MAIN_CITY.get(country_code, None)
        return {
            'GEONAMES_USERNAME':_settings.GEONAMES_USERNAME,
            'FULL_DOMAIN':_settings.FULL_DOMAIN,
            'DOMAIN':_settings.DOMAIN,
            'SUBDOMAIN_AUTHORS': _settings.SUBDOMAIN_AUTHORS,
            'MAIN_CITY': main_city,
            'IS_MOBILE': bool(self.request.is_mobile),
            'IS_OAUTH': bool(self.request.is_oauth),
            'FORCE_SSL_LOGIN': _settings.FORCE_SSL_LOGIN,
        }

class GeoContext(BaseContext):
    def get_profile(self):
        return self.request.user.is_authenticated() and \
                self.request.user.get_profile() or None

    def country_code(self):
        try:
            p = self.get_profile()
            # middlewares are not executed for error pages, so:
            geo = getattr(self.request, 'geo', None) or {}
            return p and p.country or geo.get('country_code')
        except AttributeError, e:
            logger.error(unicode(e))
            return _settings.COUNTRY_CODE

    def is_country_supported(self):
        return self.country_code() in _settings.COUNTRIES_WITH_SHOWTIMES

    def timezone(self):
        try:
            return self.request.timezone
        except AttributeError, e:
            logger.error(unicode(e))
            from film20.geo.models import BaseTimeZone
            return BaseTimeZone.tzid_for_country(_settings.COUNTRY_CODE)

def global_context(request):
    return {
        'global':GlobalContext(request),
        'geo':GeoContext(request),
        'now': datetime.datetime.now(),
    }

