#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

import os, time

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from film20.core.urlresolvers import make_absolute_url
try:
    # django 1.3 and higher
    from django.core.cache import patch_vary_headers
except ImportError:
    # django 1.2
    from django.utils.cache import patch_vary_headers

from film20.core import rating_helper
from film20.core.models import TemporaryUser

import re
import logging
logger = logging.getLogger(__name__)
request_logger = logging.getLogger('request')
api_request_logger = logging.getLogger('api')

LOGIN_URL = getattr(settings, "MAX_USERNAME_LENGTH_DISPLAY", "/account/login/")
LOCAL = getattr(settings, "LOCAL", False)
DEV = getattr(settings, "DEV", False)
LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", 'en')
ANALYTICS_CODE = getattr(settings, "ANALYTICS_CODE", '')

class LazyUniqueUser(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_unique_user'):
            if request.user.is_authenticated():
                request._unique_user = request.user
            else:
                request._unique_user = TemporaryUser.create_from_request(request)
        return request._unique_user

class LazyGoal(object):
    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_goal'):
            from film20.badges.models import Goal
            request._goal = Goal.from_request(request)
        return request._goal

class CoreMiddleware(object):    
    def process_request(self, request):        
        request.lang = LANGUAGE_CODE
        request.dev = DEV
        request.analytics_code = ANALYTICS_CODE
        request.login_url = LOGIN_URL
        request.local = LOCAL

        request.__class__.unique_user = LazyUniqueUser()
        request.__class__.goal = LazyGoal()

    def process_response(self, request, response):
        if hasattr(request, '_unique_user'):
            # request.unique_user has been accessed, store id in cookie
            if isinstance(request._unique_user, TemporaryUser):
                request._unique_user.store(response)
                patch_vary_headers(response, ('Cookie', ))
        return response

class ForceSSLLogin(object):
    SECURE_PREFIXES = ("acct_login", "acct_signup", "fbapp")

    def process_request(self, request):
        if not request.path.startswith('/api/') and settings.FORCE_SSL_LOGIN and request.method == 'GET':
            is_secure = request.META.get('SERVER_PORT') == '443'
            need_secure = any(request.path.startswith(reverse(p)) for p in self.SECURE_PREFIXES)
            if is_secure ^ need_secure:
                secure_url = make_absolute_url(request.build_absolute_uri(), secure=need_secure)
                return HttpResponseRedirect(secure_url)

class DevMiddleware(object):
    """
    Redirects to filmaster.pl from dev home page (if "test" parameter is not passed)
    Otherwise, serves regular pages.
    To be used on dev version of Filmaster only.
    """
    def process_request(self, request):
        if request.path == '/':
            try:
                if request.GET['test']:
                    pass
                else:
                    return HttpResponseRedirect('http://filmaster.pl') 
            except:
                return HttpResponseRedirect('http://filmaster.pl') 

class SubdomainMiddleware( object ):
    def process_request(self, request):
        domain = getattr(settings, "DOMAIN")
        host = request.get_host()
        if host.endswith('.'+domain):
            request.subdomain = host[:-len(domain)-1]
            if request.subdomain == 'api':
                request.path_info = '/api' + request.path_info
                request.subdomain = None
                request._api = True
            elif request.subdomain == 'secure':
                request.subdomain = None
        else:
            request.subdomain = None

    IGNORE_RE = re.compile('/static/')
    def process_response(self, request, response):
        path = request.get_full_path() or ''
        ip = request.META.get('REMOTE_ADDR')
        def log(logger):
            logger.info("[%s] %s %s (%s) %r", ip, request.method, path, response.status_code, request.META.get('HTTP_USER_AGENT', ''))
        if getattr(request, "_api", False) or path.startswith('/oauth/'):
            # do not update cache in UpdateCacheMiddleware for api subdomain
            request._cache_update_cache = False
            log(api_request_logger)
        else:
            if not self.IGNORE_RE.match(path):
                log(request_logger)
        patch_vary_headers(response, ('Host', ))
        return response

    def process_exception(self, request, exception):
        # log exceptions for easier debugging
        if not isinstance(exception, Http404):
            logger.exception(exception)
        else:
            if getattr(request, '_api', False):
                return HttpResponse("404 - Not Found")

# compile regexps
USER_AGENTS = tuple((re.compile(s), name) for (s, name) in settings.USER_AGENTS)
    

def get_theme(request):
    return settings.FORCE_OAUTH_THEME or request.GET.get('theme')

class ClientPlatform(object):
    def process_request(self, request):
        request.is_oauth = (request.path_info == '/oauth/authorize/') or request.GET.get('oauth', '')
        request.platform = 'www'
        request.is_mobile = False
        ua = request.META.get('HTTP_USER_AGENT', '')
        for r, name in USER_AGENTS:
            if r.search(ua):
                request.platform = name
                request.is_mobile = True
                break
        theme = get_theme(request) or request.COOKIES.get('theme')
        if theme:
            request.platform = theme
            request.is_mobile = True

        # temporary disable redirect to non-working /mobile/ page
        """
        if request.is_mobile and request.path == '/':
            if not request.COOKIES.get('visited', False) and not request.is_oauth:
                from urllib import urlencode
                next = urlencode([('next', request.path)])
                response = HttpResponseRedirect('/mobile/?' + next)
                response.set_cookie('visited', 'visited', max_age=365*24*3600*5)
                return response
        """

    def process_response(self, request, response):
        theme = get_theme(request)
        if theme:
            response.set_cookie('theme', theme)
        return response

from base64 import b64decode
import re

class BetaMiddleware(object):
    ALLOW_RE = re.compile('^/(static|jsi18n)/')
    
    def check_auth(self, request):

        if getattr(request, '_api', False):
            return True
        
        credentials = settings.BETA_CREDENTIALS
        if not credentials:
            return True
            
        if self.ALLOW_RE.match(request.path):
            return True
        
        logger.info(request.session.items())
        
        if 'beta_allowed' in request.session:
            return True

        credentials = settings.BETA_CREDENTIALS.split(':')
        
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Basic '):
            return False

        cred = b64decode(auth_header[6:].strip())
        allowed = re.match(settings.BETA_CREDENTIALS, cred)
        if allowed:
            request.session['beta_allowed'] = True
        
        return allowed
        
        
    def process_request(self, request):
        if not self.check_auth(request):
            from django.http import HttpResponse
            from django.template import RequestContext
            from django.template.loader import render_to_string
            out = render_to_string(
                "account/beta_access_denied.html",
                context_instance=RequestContext(request),
            )
            response = HttpResponse(out, status=401)
            response['WWW-Authenticate'] = 'Basic realm="Filmaster beta"'
            return response

from .signals import post_commit
from threading import local
_thread_local = local()

class PostCommitMiddleware(object):
    def process_request(self, request):
        _thread_local.saved_objects = []

    def process_response(self, request, response):
        saved_objects = getattr(_thread_local, 'saved_objects', ())
        if saved_objects:
            for (sender, instance, created, raw) in saved_objects:
                post_commit.send(
                        sender,
                        instance=instance,
                        created=created,
                        raw=raw)
                logger.debug('post_commit: %r', instance, extra={'bg': 'green'})
            _thread_local.saved_objects = None
        return response
    
    def process_exception(self, request, exception):
        _thread_local.saved_objects = None

    @classmethod
    def post_save(cls, sender, instance, created, raw, **kw):
        saved_objects = getattr(_thread_local, 'saved_objects', None)
        if isinstance(saved_objects, list):
            saved_objects.append((sender, instance, created, raw))
        else:
            post_commit.send(
                    sender,
                    instance=instance,
                    created=created,
                    raw=raw)
#            logger.debug('instant post_commit: %r', (instance, created, raw), extra={'bg': 'green'})

