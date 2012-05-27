from piston import forms
import oauth
import re

from film20.utils.utils import direct_to_template
from film20.core.models import User
from django import http
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_str

import logging
logger = logging.getLogger('film20.account')

def oauth_auth(request, token, callback, params):
    form = forms.OAuthAuthenticationForm(initial={
        'oauth_token': token.key,
        'authorize_access': True,
        'oauth_callback': token.get_callback_url() or callback,
      })

    return direct_to_template(request, 'piston/authorize_token.html', { 'form': form, 'token': token })

def mobile_stats(request):
    if getattr(request, 'is_mobile', False):
        profile = request.user.get_profile()
        profile.mobile_platform = getattr(request, 'platform', None)
        import datetime
        now = datetime.datetime.now()
        if not profile.mobile_first_login_at:
            profile.mobile_first_login_at = now
        profile.mobile_last_login_at = now
        profile.mobile_login_cnt += 1
        profile.save()
        logger.info("oauth %s login completed, cnt: %s", profile.mobile_platform, profile.mobile_login_cnt)
    else:
        logger.info("oauth login completed")

def login_required2(view):
    def wrapper(request):
        if not request.user.is_authenticated():
            tmp_user = request.GET.get('tmp_user')
            params = dict(
                oauth=1,
                next=request.get_full_path(),
            )
            if tmp_user:
                params['tmp_user'] = tmp_user
            login_view = reverse(tmp_user and 'acct_signup' or 'acct_login')
            from urllib import urlencode
            return HttpResponseRedirect(login_view + '?' + urlencode(params))
        return view(request)    
    return wrapper
    
@login_required2
def oauth_user_auth(request):
    from piston.authentication import oauth_user_auth as _oauth_user_auth
    response = _oauth_user_auth(request)
    if request.POST:
        if isinstance(response, HttpResponseRedirect):
            if not '?error=' in response['location']:
                mobile_stats(request)
            logger.info("redirect to: %s", response['location'])
        else:
            logger.debug("no redirect")
    else:
        logger.info("waiting for user token authorization...")
    return response

class Http401(Exception):
    pass

def create_fb_user(request):
    from film20.facebook_connect.views import auto_create_fb_user
    access_token = request.REQUEST.get('access_token')
    try:
        return auto_create_fb_user(request, access_token)
    except Exception, e:
        raise Http401(unicode(e))

def create_anon_user(request):
    username = request.REQUEST.get('username', '')
    password = request.REQUEST.get('password', '')

    if not re.match("\w{3}-[0-9a-f]{20,26}$", username, re.I):
        raise Http401("invalid username")

    if len(password) < 20:
        raise Http401("invalid password")

    user, created = User.objects.get_or_create(username=username, is_active=False)
    if created:
        user.set_password(password)
        user.save()
    else:
        if not user.check_password(password):
            raise Http401("invalid password")

    return user

def oauth_user_auth_anon(request, method):
    from piston.authentication import initialize_server_request, send_oauth_error, get_callable, INVALID_PARAMS_RESPONSE
    oauth_server, oauth_request = initialize_server_request(request)

    if oauth_request is None:
        logger.error("OAuth: INVALID_PARAMS_RESPONSE")
        return INVALID_PARAMS_RESPONSE

    try:
        token = oauth_server.fetch_request_token(oauth_request)
        if token is None:
            raise oauth.OAuthError("no token")
    except oauth.OAuthError, err:
        logger.error("OAuthError: %s", err.message)
        return send_oauth_error(err)

    try:
        callback = oauth_server.get_callback(oauth_request)
    except:
        callback = None

    create_user = globals().get('create_%s_user' % method)
    if not create_user:
        raise http.Http404

    try:
        user = create_user(request)
    except Http401, e:
        logger.warning(unicode(e))
        return http.HttpResponse(smart_str(e), status=401)

    token = oauth_server.authorize_token(token, user)

    args = token.to_string(only_key=True)
    if not callback:
        return http.HttpResponse(args)

    return http.HttpResponseRedirect(callback + '?' + args)

def oauth_pin(request, token):
    from django.http import HttpResponse
    return direct_to_template(request, 'piston/show_pin.html', {'token': token})

def handler404(request):
    return HttpResponseNotFound("not found")

