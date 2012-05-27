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
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import simplejson as json
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from film20.utils.utils import is_mobile
import urllib2
from urllib import urlencode
import oauth
import logging
logger = logging.getLogger(__name__)

import oauth
class OAuthService(object):
    signature = oauth.OAuthSignatureMethod_HMAC_SHA1()
    
    def get_access_token(self, user):
        raise NotImplementedError()

    def get_user_id(self, user):
        raise NotImplementedError()
    
    def set_access_token(self, user, token, user_id):
        raise NotImplementedError()

    def __init__(self, name, key, secret, extra_key=None, extra_secret=None):
        self.name = name
        self.normalized_name = self.normalize_name(name)
        self.consumer = oauth.OAuthConsumer(key, secret)

        self.consumers = dict()
        self.consumers[key] = self.consumer

        if extra_key and extra_secret:
            self.consumers[extra_key] = oauth.OAuthConsumer(extra_key, extra_secret)

    @classmethod
    def normalize_name(cls, name):
        return name.lower()

    class NotFound(Exception):
        pass

    class Error(Exception):
        pass
    
    @classmethod
    def get_by_name(cls, name):
        name = cls.normalize_name(name)
        for service in OAUTH_SERVICES:
            if service.normalized_name == name:
                return service
        raise cls.NotFound("service %s not found" % name)
    
    def begin(self, request, callback_url):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, callback=callback_url, http_url=self.REQUEST_TOKEN_URL)
        oauth_request.sign_request(self.signature, self.consumer, None)

        url = oauth_request.to_url()
        req = urllib2.Request(url)

        try:
            data = urllib2.urlopen(req)
        except Exception, e:
            logger.exception(e)
            raise

        resp = data.read()
        token = oauth.OAuthToken.from_string(resp)

        from film20.utils.utils import is_mobile

        mobile = is_mobile(request)
        if mobile:
            url = getattr(self, 'AUTHORIZE_URL_MOBILE', self.AUTHORIZE_URL)
        else:
            url = self.AUTHORIZE_URL
             
        oauth_request = oauth.OAuthRequest.from_token_and_callback(token = token, http_url = url)

        request.session['%s_unauth_access_token' % self.normalized_name] = str(token)
        logger.debug("unauth token stored in session %r", request.session.session_key)
#        request.session.save()
        return HttpResponseRedirect(oauth_request.to_url())

    def associate(self, request):
        callback_url = settings.FULL_DOMAIN + reverse('oauth_assoc_callback', args=[self.normalized_name])
        return self.begin(request, callback_url)
        
    def login(self, request, next=None):
        callback_url = settings.FULL_DOMAIN + reverse('oauth_login_callback', args=[self.normalized_name])
        if next:
            callback_url += '?' + request.META.get('QUERY_STRING') #urlencode({'next':next})
        return self.begin(request, callback_url)

    def fetch_access_token(self, request):
        oauth_token=request.GET.get('oauth_token')
        oauth_verifier = request.GET.get('oauth_verifier')
        if oauth_token is None or oauth_verifier is None: 
            raise self.Error(request.GET.get('error') or 'Invalid request parameters')

        token = request.session.get('%s_unauth_access_token' % self.normalized_name)
        if not token:
            raise self.Error(_("invalid session data"))
        token = oauth.OAuthToken.from_string(token)

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=token, verifier=oauth_verifier, http_url = self.ACCESS_TOKEN_URL)
        oauth_request.sign_request(self.signature, self.consumer, token)
        req = urllib2.Request(oauth_request.to_url())
        data = urllib2.urlopen(req)
        token = data.read()

        access_token = oauth.OAuthToken.from_string(token)
        logger.debug("%s access token: %s", self.name, access_token.to_string())
        return access_token

    def associate_url(self):
        return settings.FULL_DOMAIN + reverse('oauth_associate', args=[self.normalized_name])
    
    def cancel_url(self):
        return settings.FULL_DOMAIN + reverse('oauth_cancel', args=[self.normalized_name])
    
    def get_opener(self, token):
        from utils.auth import oauth_opener
        if '|' in token:
            key, token = token.split('|')
            consumer = self.consumers[key]
        else:
            consumer = self.consumer
        token = oauth.OAuthToken.from_string(token)
        return oauth_opener(consumer, token)

    class ServiceAlreadyAssociated(Exception):
        pass

from film20.core.models import LocalizedProfile

class TwitterService(OAuthService):
    REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
    ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
    AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize"

    def get_access_token(self, user):
        return user.get_profile().twitter_access_token

    def get_user_id(self, user):
        return user.get_profile().twitter_user_id
    
    def get_user_info(self, token):
        logger.debug("fetching user info for token: %r", token)
        opener = self.get_opener(token)
        data = opener.open("http://api.twitter.com/1/account/verify_credentials.json").read()
        data = json.loads(data)
        logger.debug(data)
        info = dict(
            user_id = data.get('screen_name'),
            username = data.get('screen_name'),
            avatar_url = data.get('profile_image_url'),
        )
        logger.debug('%s user info: %s', self.normalized_name, info)
        return info
    
    def post(self, token, status):
        input = dict(
            status=status,
        )
        opener = self.get_opener(token)
        input = urlencode(input)
        logger.debug(input)
        data = opener.open("http://api.twitter.com/1/statuses/update.json", input).read()
        data = json.loads(data)
        logger.debug("reply: %r", data)
    
    def set_access_token(self, user, token, user_id):
        profile = user.get_profile()
        profile.twitter_access_token = token
        profile.twitter_user_id = user_id
        profile.save()
        return True

    def get_user(self, user_id):
        return User.objects.get(profile__twitter_user_id=user_id)

class FourSquareService(OAuthService):
    REQUEST_TOKEN_URL = "http://foursquare.com/oauth/request_token"
    ACCESS_TOKEN_URL = "http://foursquare.com/oauth/access_token"
    AUTHORIZE_URL = "http://foursquare.com/oauth/authorize"

    def get_access_token(self, user):
        return user.get_profile().foursquare_access_token
    
    def get_user_id(self, user):
        return user.get_profile().foursquare_user_id

    def get_user_info(self, token):
        opener = self.get_opener(token)
        data = opener.open("http://api.foursquare.com/v1/user.json").read()
        data = json.loads(data)
        logger.debug(data)
        info = dict(
            user_id = str(data['user']['id']),
            username = ("%(firstname)s %(lastname)s" % data['user']).strip(),
            avatar_url = data['user']['photo'],
            email = data['user']['email'],
        )
        return info

    def set_access_token(self, user, token, user_id):
        profile = user.get_profile()
        profile.foursquare_access_token = token
        profile.foursquare_user_id = user_id
        profile.save()
        return True

    def get_user(self, user_id):
        return User.objects.get(profile__foursquare_user_id=user_id)

OAUTH_SERVICES = ()
if getattr(settings, 'TWITTER_KEY', None):
    if hasattr(settings, 'TWITTER_EXTRA_KEY'):
        extra = (settings.TWITTER_EXTRA_KEY, settings.TWITTER_EXTRA_SECRET)
    else:
        extra = ()
    OAUTH_SERVICES += TwitterService("Twitter", settings.TWITTER_KEY, settings.TWITTER_SECRET, *extra),
if getattr(settings, 'FOURSQUARE_KEY', None):
    OAUTH_SERVICES += FourSquareService("FourSquare", settings.FOURSQUARE_KEY, settings.FOURSQUARE_SECRET),
