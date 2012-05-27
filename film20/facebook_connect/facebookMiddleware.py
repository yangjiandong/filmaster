#!/usr/bin/python
# Diamanda Application Set
# User Panel
import urllib2
from datetime import datetime, date
from hashlib import md5
from random import choice
import os
import os.path

from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.contrib.auth import logout

from film20.facebook_connect.models import *
from film20.userprofile.models import Avatar
from film20.utils.slughifi import slughifi

import logging
logger = logging.getLogger(__name__)

class LazyFBAssociation(object):
    def __get__(self, request, obj_type=None):
        if hasattr(request, '_fb_association'):
            return request._fb_association
        assoc = None
        if request.user.is_authenticated():
            try:
                assoc = FBAssociation.objects.get(user=request.user)
            except FBAssociation.DoesNotExist, e:
                pass
        request._fb_association = assoc
        return assoc

class fbMiddleware(object):
    """
    Parse and check sigature of Facebook cookie and stores some fields in request
    """
    def process_request(self, request):
        request.facebookconn = False
        request.facebookconn_new = False
        f_name = False
        l_name = False
        # Check if we have the FBConnect cookie
        cookie = self.get_facebook_cookie(request, settings.FACEBOOK_CONNECT_KEY, settings.FACEBOOK_CONNECT_SECRET)
        request.fbcookie = cookie
        request.facebookconn = cookie and cookie['uid']

        request.__class__.fb_association = LazyFBAssociation() 

    def get_facebook_cookie(self, request, app_id, secret):
        import cgi, hashlib
        cookie = request.COOKIES.get('fbs_' + app_id)
        if not cookie:
            return
        parsed = sorted(cgi.parse_qsl(cookie.strip('"')), key=lambda x:x[0])
        ret = dict(parsed)
        s = ''.join("%s=%s"%t for t in parsed if t[0]!='sig')
        if hashlib.md5(s + secret).hexdigest().lower()==ret['sig'].lower():
            return ret
        
