#!/usr/bin/python
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
from datetime import datetime, timedelta, date
import time
import logging
logger = logging.getLogger(__name__)
auth_logger = logging.getLogger('film20.account')

from random import choice

from django.conf import settings
from django.shortcuts import render_to_response
from django.views.generic.simple import direct_to_template
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from film20.core.urlresolvers import reverse as abs_reverse
from django.core.urlresolvers import reverse

from film20.facebook_connect.models import *
from film20.userprofile.models import Avatar
from film20.config.urls import *

from django.utils import simplejson as json
import urllib2
from urllib import urlencode
from cgi import parse_qsl

import re
try:
    from PIL import Image
except:
    import Image
import os
import os.path

import base64, pickle

from .utils import get_facebook_cookie
from .graph import API

def get_access_token(code, app_id, secret, redirect_uri=''):
    params = dict(
        client_id = settings.FACEBOOK_CONNECT_KEY,
        client_secret = settings.FACEBOOK_CONNECT_SECRET,
        redirect_uri=redirect_uri,
        code=code,
    )
    url = "https://graph.facebook.com/oauth/access_token"
    params = dict(parse_qsl(urllib2.urlopen(url, urlencode(params)).read()))
    access_token = params.get('access_token')
    return access_token

def show_login(request):
    return render_to_response(
        'facebook_connect/show_login.html',
        {},
        context_instance=RequestContext(request))

def facebook_user_details(access_token):
    data = dict(
        access_token=access_token,
    )
    me_url = 'https://graph.facebook.com/me?'+urlencode(data)
    reply = json.loads(urllib2.urlopen(me_url).read())
    email = reply.get('email')
    name = reply.get('name')
    uid = reply.get('id')
    username=reply.get('username', '')
    first_name=reply.get('first_name', '')
    last_name=reply.get('last_name', '')

    picture_url = "http://graph.facebook.com/%s/picture?type=large" % uid
    
    return dict(
        email=email,
        username=username,
        first_name=first_name,
        last_name=last_name,
        name=name,
        avatar_url=picture_url,
        uid=uid,
        id=uid,
    )

def fb_begin(request, redirect_uri = None):
    params = dict(
      client_id = settings.FACEBOOK_CONNECT_KEY,
      redirect_uri=redirect_uri or abs_reverse(fb_auth_cb),
      state=request.META.get('QUERY_STRING', ''),
      scope=settings.FACEBOOK_PERMS,
    )
    if request.is_mobile:
        params['display'] = 'touch'
    return HttpResponseRedirect('https://graph.facebook.com/oauth/authorize?' + urlencode(params))

def fb_error(request):
    return direct_to_template(request, 'facebook_connect/fb_error.html', {
        'error_description': "Facebook error: %(descr)s" % {'descr':request.GET.get('descr', '')},
    })

def catch_exception(view):
    def wrapper(request, *args, **kw):
        try:
            return view(request, *args, **kw)
        except Exception, e:
            qs = request.META.get('QUERY_STRING', '')
            auth_logger.error("Facebook error: %(descr)s" % {'descr':unicode(e)})
            auth_logger.exception(e)
            err = urlencode(dict(descr=unicode(e)))
            return HttpResponseRedirect(reverse(fb_error) + '?' + qs + '&' + err)
    return wrapper

class AutoCreateException(Exception):
    pass

from film20.emailconfirmation.models import EmailAddress

def auto_create_fb_user(request, access_token, username=None):
    from film20.account.forms import clean_username, SSORegistrationForm
    user_details = facebook_user_details(access_token)
    uid = user_details['uid']
    try:
        association = FBAssociation.objects.get(fb_uid=uid)
        if association.access_token != access_token:
            association.access_token = access_token
            if getattr(association, 'status', 0) >= 400:
                association.status = 0
            association.save()
        return association.user
    except FBAssociation.DoesNotExist, e:
        pass

    email = user_details.get('email')
    if not email:
        raise AutoCreateException('invalid registration data: no email address')

    try:
        ea = EmailAddress.objects.get(email=email, verified=True)
        user = ea.user
    except EmailAddress.DoesNotExist:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

    is_new = not bool(user)

    if user:
        # check if user associated with email from fb has association already
        try:
            assoc = FBAssociation.objects.get(user=user)
            return user
        except FBAssociation.DoesNotExist, e:
            pass

    if not user:
        if username:
            data = dict(username=username, email=email)
            form = SSORegistrationForm(data, request=request)
            if not form.is_valid():
                raise AutoCreateException('invalid registration data: %r' % form.errors)
            user = form.save()
        else:
            username = user_details.get('username') or user_details.get('name', '')

            username = username and clean_username(username)

            try_cnt = 0

            while try_cnt < 100:
                data = dict(
                        username=username + (try_cnt and str(try_cnt) or ""),
                        email=email,
                )
                form = SSORegistrationForm(data, request=request)
                if form.is_valid():
                    user = form.save()
                    logger.info("user created: %r", user)
                    break
                try_cnt += 1

    if user:
        # associate with fb
        FBAssociation.objects.create(user=user, fb_uid=uid, is_new=is_new, access_token=access_token)
        return user
    else:
        raise AutoCreateException("invalid registration data: %r" % form.errors)


@catch_exception
def fb_auth_cb(request):
    if request.GET.get('error'):
        raise Exception(request.GET.get('error_description', 'unknown'))
    if 'code' in request.GET:
        query_string = request.GET.get('state', '')
        access_token = get_access_token(
                request.GET.get('code'),
                settings.FACEBOOK_CONNECT_KEY,
                settings.FACEBOOK_CONNECT_SECRET,
                settings.FULL_DOMAIN + reverse(fb_auth_cb))
        user_details = facebook_user_details(access_token)
        uid = user_details['uid']
    else:
        query_string = request.META.get('QUERY_STRING', '')
        cookie = get_facebook_cookie(request)
        if not cookie:
            logger.error("No FB cookie !")
            return HttpResponseRedirect(reverse("acct_login") + "?" + query_string)
        uid = cookie['user_id']
        access_token = get_access_token(cookie['code'], settings.FACEBOOK_CONNECT_KEY, settings.FACEBOOK_CONNECT_SECRET)
        user_details = None
    try:
        association = FBAssociation.objects.get(fb_uid=uid)
        if association.access_token != access_token:
            association.access_token = access_token
            if getattr(association, 'status', 0) >= 400:
                association.status = 0
            association.save()
        if not association.user.is_active:
            raise Exception(_("Account is inactive"))
        user = authenticate(fb_uid=uid)
        login(request, user)
        qs = dict(parse_qsl(query_string))
        next = qs.get('next', '/')
        return HttpResponseRedirect(next)
    except FBAssociation.DoesNotExist, e:
        pass

    if not user_details:
        user_details = facebook_user_details(access_token)

    request.session['facebook_reg_data'] = dict(
        user_details=user_details,
        access_token=access_token,
    )

    return HttpResponseRedirect(reverse(fb_register_user) + '?' + query_string)

def fb_register_user(request):
    from film20.account.views import get_next, new_user_registered_redirect
    from film20.account.forms import SSORegistrationForm
    reg_data = request.session.get('facebook_reg_data')
    if not reg_data:
        return HttpResponse("No reg data", status=400)
    user_details = reg_data['user_details']
    access_token = reg_data['access_token']

    fb_user = FBUser.create_or_update(user_details)
    user_details['avatar_url'] = fb_user.picture_url('large')
    
    uid = user_details['uid']
    next = get_next(request)
    if request.POST:
        form = SSORegistrationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            assoc = FBAssociation(user=user, fb_uid=uid, is_new=True, is_from_facebook=True, access_token=access_token)
            assoc.save()
            try:
                Avatar.create_from_url(user, user_details['avatar_url'])
            except Exception, e:
                logger.debug(e)
            user = authenticate(fb_uid=uid)
            login(request, user)
            return new_user_registered_redirect(request, next)
    else:
        initial = dict(
            next=next,
            username=user_details.get('username') or user_details.get('name', ''),
            email=user_details.get('email', ''),
        )
        form = SSORegistrationForm(initial=initial, request=request)

    return direct_to_template(request, "account/sso_registration.html", {
        'form':form,
        'user_info':user_details,
    })

@login_required
@catch_exception
def assign_facebook(request):
    if request.GET.get('error'):
        err = dict(error=request.GET.get('error'))
        return HttpResponseRedirect(reverse('associations') + '?' + urlencode(err))
    cookie = get_facebook_cookie(request)
    if cookie:
        uid = cookie['user_id']
        access_token = get_access_token(cookie['code'], settings.FACEBOOK_CONNECT_KEY, settings.FACEBOOK_CONNECT_SECRET)
        user_details = API().get("/%s" % uid)
        logger.info(user_details)
    elif 'code' in request.GET:
        query_string = request.GET.get('state', '')
        access_token = get_access_token(
                request.GET.get('code'),
                settings.FACEBOOK_CONNECT_KEY,
                settings.FACEBOOK_CONNECT_SECRET,
                settings.FULL_DOMAIN + reverse(assign_facebook))
        user_details = facebook_user_details(access_token)
        uid = user_details['uid']
    else:
        return fb_begin(request, redirect_uri=abs_reverse(assign_facebook))
        
    try:
        assoc = FBAssociation.objects.get(user=request.user)
        err = dict(error=_("%s already has fb association") % request.user)
        return HttpResponseRedirect(reverse('associations') + '?' + urlencode(err))
    except FBAssociation.DoesNotExist:
        pass

    try:
        assoc = FBAssociation.objects.get(fb_uid=uid)
        msg=_("This %(service)s service account is already associated with user %(user)s") % dict(service='facebook', user=assoc.user)
        err = dict(error=msg.encode('utf-8'))
        return HttpResponseRedirect(reverse('associations') + '?' + urlencode(err))
    except FBAssociation.DoesNotExist:
        pass
    assoc = FBAssociation.objects.create(
        user=request.user, 
        fb_uid=uid, 
        fb_user=FBUser.create_or_update(user_details),
        is_new=False, 
        access_token=access_token,
        is_from_facebook=False
    )
    return HttpResponseRedirect(reverse('associations') + '?associated')

@login_required
def unassign_facebook(request):
    from django.contrib.auth import BACKEND_SESSION_KEY, load_backend
    from film20.facebook_connect.facebookAuth import FacebookBackend
    
    backend = load_backend(request.session[BACKEND_SESSION_KEY])
    if isinstance(backend, FacebookBackend):
        return HttpResponse("Can't remove association if you are logged in with FB")

    FBAssociation.objects.filter(user=request.user).delete()
    return HttpResponseRedirect(reverse('associations') + '?unassociated')

from .models import LikeCounter

from film20.core.deferred import defer

def fb_like(request):
    url = request.POST.get('url')
    content_type=request.POST.get('content_type')
    object_id = request.POST.get('object_id')
    
    if not (url and content_type and object_id):
        return HttpResponse(status=400)
    
    defer(LikeCounter.update, url, content_type, object_id)

    return HttpResponse('ok')

def store_request(request):
    id = request.POST.get('id')
    data = request.POST.get('data')
    sender = request.user

    if not id or not data or sender.is_anonymous():
        return HttpResponse('error', status=400)

    FBRequest.objects.get_or_create(id=id, data=data, sender=sender)

    return HttpResponse('ok')


