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
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.template import RequestContext
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from film20.core.urlresolvers import reverse as abs_reverse, make_absolute_url
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
#from film20.account.auth_login import login as auth_login

from forms import SignupForm, AddEmailForm, LoginForm, ResetPasswordForm, OpenIDForm
from film20.emailconfirmation.models import EmailAddress, EmailConfirmation
from film20.core.models import Profile

from film20.config.urls import *
from film20.userprofile.models import Avatar
from film20.utils.utils import JSONResponse, is_ajax
from film20.facebook_connect.models import FBAssociation
from django_openidauth.models import UserOpenID, associate_openid, unassociate_openid
from django_openidconsumer import views as openid_consumer_views
from django.utils import simplejson as json
from urllib import urlencode

import logging
logger = logging.getLogger(__name__)
from django.forms.util import ErrorList

# UserAgent-aware direct_to_template version
from film20.utils.utils import direct_to_template
import urllib2

DOMAIN = getattr(settings, "DOMAIN", '')
FULL_DOMAIN = getattr(settings, "FULL_DOMAIN", '')

def get_next(request):
    next = request.REQUEST.get('next', '')
    return next

def new_user_registered_url(request, next):
    is_oauth = getattr(request, 'is_oauth', True)
    if not is_oauth:
        profile = request.unique_user.id and request.unique_user.get_profile()
        if profile and profile.has_recommendations():
            next = reverse('main_page')
        else:
            next = reverse('rate_films')
    return make_absolute_url(next or '/')

def new_user_registered_redirect(request, next):
    return HttpResponseRedirect(new_user_registered_url(request, next))

def logout(request):
    next = request.GET.get('next', '')
    logger.info(next)
    if next:
        auth_logout(request)
        return HttpResponseRedirect(next)
    else:
        from django.contrib.auth.views import logout as logout_view
        return logout_view(request, template_name='account/logout.html')
        
@never_cache
def login(request):
    reason = None
    next = request.REQUEST.get('next', '')

    if request.method == "POST":
        openidform = OpenIDForm(request.POST)
        def openid_failure(request,message):
          return direct_to_template(request, "account/login.html", {
            "form": LoginForm(),
            "openidform": openidform,
            "openid_message":message,
            "reason": reason,
          })

        def if_not_user_url(request):
          return HttpResponseRedirect(reverse('acct_login'))

        if request.POST.has_key('openid_url'):
            redirect_to = '/openid/complete/'
            if next:
                logger.info("NEXT: %s", next)
                redirect_to += '?' + urlencode({'next':next})
            return openid_consumer_views.begin(request,on_failure=openid_failure,sreg = 'email,nickname',redirect_to=redirect_to, if_not_user_url=if_not_user_url)
          
        form = LoginForm(request.POST)
        redirect_to = None
        if form.login(request):	                
            return HttpResponseRedirect(make_absolute_url(next or '/'))
    else:        
        # http://jira.filmaster.org/browse/FLM-420
        full_next = FULL_DOMAIN + next
        if next == full_url("LOGOUT") or full_next == full_url("LOGOUT"):
            next = ""
        reason = request.GET.get('reason')
            
        form = LoginForm(
            initial = {
                'next': next,
                'reason': reason,
        })

        openidform = OpenIDForm(
            initial = {
                'next': next,
                'reason': reason,
        })
        
    return direct_to_template(request, "account/login.html", {
        "next": next,
        "form": form,
        "openidform": openidform,
        "reason": reason, 
    })

def signup(request):
    reason = None
    next = get_next(request)
    iframe = 'iframe' in request.GET
    template = "account/%ssignup.html" % (iframe and 'iframe_' or '')
    
    if request.method == "POST":
        openidform = OpenIDForm(request.POST)
        def openid_failure(request,message):
            return direct_to_template(request, template, {
                "form": SignupForm(request=request),
                "openidform": openidform,
                "openid_message":message,
                "next":next,
                "reason": reason,
            })

        def if_not_user_url(request):
            return HttpResponseRedirect(reverse('acct_login'))

        if request.POST.has_key('openid_url'):
            from urllib import urlencode
            return openid_consumer_views.begin(request,on_failure=openid_failure,sreg = 'email,nickname',redirect_to='/openid/complete/?%s'%urlencode({'next':next or '/'}), if_not_user_url=if_not_user_url)
            
        form = SignupForm(request.POST, request=request, prefix=iframe and 'ajax' or None)
        if form.is_valid():
            user = form.save()
            user = authenticate(username=user.username, password=form.cleaned_data['password1'])
            auth_login(request, user)
            if iframe:
                return HttpResponse('<script>top.location.href = "%s";</script>' % make_absolute_url(next or '/'))
            return new_user_registered_redirect(request, next or '/')
    else:
        form = SignupForm(request=request, prefix=iframe and 'ajax' or None)
    openidform = OpenIDForm(
        initial = {
            'next': next,
            'reason': reason,
    })
    return direct_to_template(request, template, {
        "form": form,
        "next": next,
        "openidform": openidform,
    })

@login_required
def email(request):
    if request.method == "POST" and request.user.is_authenticated():
        if request.POST["action"] == "add":
            add_email_form = AddEmailForm(request.user, request.POST)
            if add_email_form.is_valid():
                add_email_form.save()
                add_email_form = AddEmailForm() # @@@
        else:
            add_email_form = AddEmailForm()
            if request.POST["action"] == "send":
                email = request.POST["email"]
                try:
                    email_address = EmailAddress.objects.get(user=request.user, email=email)
                    request.user.message_set.create(message="Confirmation email sent to %s" % email)
                    EmailConfirmation.objects.send_confirmation(email_address)
                except EmailAddress.DoesNotExist:
                    pass
            elif request.POST["action"] == "remove":
                email = request.POST["email"]
                try:
                    email_address = EmailAddress.objects.get(user=request.user, email=email)
                    email_address.delete()
                    request.user.message_set.create(message="Removed email address %s" % email)
                except EmailAddress.DoesNotExist:
                    pass
            elif request.POST["action"] == "primary":
                email = request.POST["email"]
                email_address = EmailAddress.objects.get(user=request.user, email=email)
                email_address.set_as_primary()
    else:
        add_email_form = AddEmailForm()
    
    return direct_to_template(request, "account/email.html", {
        "add_email_form": add_email_form,
    })

@login_required
def password_change(request):
    if request.user.has_usable_password():
        form_class = ChangePasswordForm 
    else:
        form_class = SetPasswordForm
        
    if request.method == "POST":
        password_change_form = form_class(request.user, request.POST)
        if password_change_form.is_valid():
            password_change_form.save()
#            password_change_form = ChangePasswordForm(request.user)
            return HttpResponseRedirect(full_url("CHANGE_PASSWORD_DONE"))
    else:
        password_change_form = form_class(request.user)
    return direct_to_template(request, "account/password_change.html", {
        "password_change_form": password_change_form,
    })

def password_reset(request):
    if request.method == "POST":
        password_reset_form = ResetPasswordForm(request.POST)
        if password_reset_form.is_valid():
            email = password_reset_form.save()
            return direct_to_template(request, "account/password_reset_done.html", {
                "email": email,
            })
    else:
        password_reset_form = ResetPasswordForm()
    
    return direct_to_template(request, "account/password_reset.html", {
        "password_reset_form": password_reset_form,
    })

from gravatar.templatetags.gravatar import gravatar

def username_autocomplete(request):
    if request.user.is_authenticated():
        q = request.GET.get("q")
        friends = [] #Friendship.objects.friends_for_user(request.user)
        content = []
        for friendship in friends:
            if friendship["friend"].username.lower().startswith(q):
                try:
                    profile = friendship["friend"].get_profile()
                    entry = "%s,,%s,,%s" % (
                        gravatar(friendship["friend"], 40),
                        friendship["friend"].username,
                        profile.location
                    )
                except Profile.DoesNotExist:
                    pass
                content.append(entry)
        response = HttpResponse("\n".join(content))
    else:
        response = HttpResponseForbidden()
    setattr(response, "djangologging.suppress_output", True)
    return response

from models import OAuthService, OAUTH_SERVICES

@login_required
@never_cache
def openid_assign(request):
    user_openids = set(o.openid for o in UserOpenID.objects.filter(user=request.user).order_by('created_at'))
    last_openid = request.openids and request.openids[-1].openid
    if last_openid and last_openid not in user_openids:
        associate_openid(request.user, last_openid)
    return HttpResponseRedirect(reverse('associations'))

def oauth_catch_exception(view):
    def wrapper(request, name, *args, **kw):
        try:
            return view(request, name, *args, **kw)
        except Exception, e:
            service = OAuthService.get_by_name(name)
            logger.error("%(name)s error: %(descr)s" % {'name':service.name, 'descr':unicode(e)})
            logger.exception(e)
            return direct_to_template(request, 'account/oauth_error.html', {
                'error_description': _("%(name)s error: %(descr)s") % {'name':service.name, 'descr':unicode(e)},
            })
    return wrapper
            
@oauth_catch_exception
def oauth_associate(request, name):
    return OAuthService.get_by_name(name).associate(request)

def oauth_cancel(request, name):
    OAuthService.get_by_name(name).set_access_token(request.user, None, None)
    return HttpResponseRedirect(reverse('associations'))
    
@oauth_catch_exception
def oauth_assoc_callback(request, name):
    service = OAuthService.get_by_name(name)
    token = service.fetch_access_token(request).to_string()
    ctx = {}

    info = service.get_user_info(token)
    user_id = info['user_id']
    try:
        user = service.get_user(user_id)
        ctx['error'] = (_("This %(service)s service account is already associated with user %(user)s") % dict(service=service.name, user=user))
    except User.DoesNotExist, e:
        service.set_access_token(request.user, token, user_id)
    return HttpResponseRedirect(reverse('associations') + '?' + urlencode(ctx))

@oauth_catch_exception
def oauth_login(request, name):
    next = get_next(request)
    # TODO - some kind of next parameter validation
    ip = request.META.get('REMOTE_ADDR')
    logger.info("[%s] (%s) starting %s oauth login", ip, request.META.get('HTTP_USER_AGENT', ''), name)
    return OAuthService.get_by_name(name).login(request, next)

def auth_login_and_stats(request, user):
    auth_login(request, user)
    return
    if getattr(request, 'is_mobile', False):
        profile = user.get_profile()
        profile.mobile_platform = getattr(request, 'platform', None)
        import datetime
        now = datetime.datetime.now()
        if not profile.mobile_first_login_at:
            profile.mobile_first_login_at = now
        profile.mobile_last_login_at = now
        profile.mobile_login_cnt += 1
        profile.save()

@oauth_catch_exception
def oauth_login_callback(request, name):
    service = OAuthService.get_by_name(name)
    next = get_next(request)
    oauth = request.GET.get('oauth')
    error = request.GET.get('denied') and _("Access denied") or request.GET.get('error')
    if error:
        raise service.Error(error)
    try:
        access_token = service.fetch_access_token(request).to_string()
        user_info = service.get_user_info(access_token)
    except IOError, e:
        if hasattr(e, 'reason'):
            error = _("We failed to reach server (%s)") % e.reason
        else:
            error = _("The server couldn't fulfill the request (code: %s)") % e.code
        raise service.Error(error)
    
    user = authenticate(service=service, user_id=user_info['user_id'])
    if user:
        auth_login_and_stats(request, user)
        service.set_access_token(user, access_token, user_info['user_id'])
        logger.info("existing %s user (%s) logged in, redirecting to %r", name, user, next or '/')
        return HttpResponseRedirect(next or '/')
    
    request.session['oauth_reg_data'] = dict(
        access_token=access_token,
        user_info=user_info,
        next=next,
    )
    logger.debug("oauth_reg_data stored in session %r", request.session.session_key)

    return HttpResponseRedirect(reverse(oauth_new_user, args=[name]) + '?' + urlencode(dict(next=next, oauth=oauth)))

DASHBOARD_URL = full_url("ACCOUNT")

from film20.account.forms import SSORegistrationForm

@never_cache
@oauth_catch_exception
def oauth_new_user(request, name):
    from film20.utils.utils import direct_to_template

    logger.info("registering new %s user", name)
    
    reg_data = request.session.get('oauth_reg_data')
    access_token = reg_data['access_token']
    user_info = reg_data['user_info']
    next = reg_data['next'] or '/'
    service = OAuthService.get_by_name(name)
    
    if request.POST:
        form = SSORegistrationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            service.set_access_token(user, access_token, user_info['user_id'])
            try:
                Avatar.create_from_url(user, user_info['avatar_url'])
            except Exception, e:
                logger.warning(e)
            user = authenticate(service=service, user_id=user_info['user_id'])
            if user:
                auth_login_and_stats(request, user)
                logger.info("%s user (%s) authenticated and logged in, redirecting to %r", name, user, next)
                return new_user_registered_redirect(request, next)
            logger.error("Can't login to new created user %s" % user)
            assert False, "Can't login to new created user %s" % user
        else:
            logger.warning("invalid sso form: %s", form.errors)
    else:
        logger.debug(user_info)
        initial = dict(
            next=next,
            username=user_info.get('username'),
            email=user_info.get('email'),
        )
        form = SSORegistrationForm(initial=initial, request=request)
    return direct_to_template(request, "account/sso_registration.html", {
        'form':form,
        'user_info':user_info,
    })

def openid_new_user(request):
    next = get_next(request)
    if request.method == 'POST':
        form = SSORegistrationForm(request.POST, request=request)

        if form.is_valid():
            from django_openidauth.models import associate_openid
            from django.contrib.auth import load_backend
            new_user = form.save()
            associate_openid( new_user, request.openid )
            backend = load_backend('django.contrib.auth.backends.ModelBackend')
            new_user.backend = '%s.%s' % (
                backend.__module__, backend.__class__.__name__
            )
            auth_login(request, new_user)
            return new_user_registered_redirect(request, next or '/')
    else:
        initial = dict(
            next=next,
        )
        form = SSORegistrationForm(initial=initial, request=request)

    return direct_to_template(request, "account/sso_registration.html", {
        'form':form,
    })

