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
import re

from django import forms
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.encoding import smart_unicode

# favour django-mailer but fall back to django.core.mail
try:
    from mailer import send_mail
except ImportError:
    from django.core.mail import send_mail

from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from django.contrib.auth import login as auth_login
#from film20.account.auth_login import login as auth_login

from film20.emailconfirmation.models import EmailAddress
from film20.useractivity.models import UserActivity
from film20.core.models import Profile, Rating
from film20.core.fields import ReCaptchaField
import logging
logger = logging.getLogger(__name__)
from film20.core.urlresolvers import reverse as abs_reverse
from django.core.urlresolvers import reverse

alnum_re = re.compile(r'^\w+$')

class CleanEmailMixIn(object):
    def clean_email( self ):
        """
        Email address must be unique
        """
        email = self.cleaned_data["email"]
        if email:
            try:
                EmailAddress.objects.get(email=email, verified=True)
            except EmailAddress.DoesNotExist:
                try:
                    User.objects.get(email=email)
                except User.DoesNotExist:
                    return self.cleaned_data["email"]
            raise forms.ValidationError( _( "That email address is already taken. Please choose another." ) )

def clean_username(username):
    from film20.utils.texts import deogonkify
    return re.sub('[^\w]', '', deogonkify(unicode(username)))

class CleanUsernameMixIn(object):
    def clean_username(self):
        username = self.cleaned_data['username']
        if not alnum_re.search(username):
            raise forms.ValidationError(_("Username can only contain regular characters."))
        try:
            user = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(_("Username taken. Choose a different one."))

def add_email(user, email):
    if email:
        try:
            EmailAddress.objects.add_email(user, email)
            user.message_set.create(message=_(u"Confirmation email sent to %s") % email)
        except Exception, e:
            user.message_set.create(message=_(u"Can't send confirmation email: %s") % unicode(e))

class LoginForm(forms.Form):

    username = forms.CharField(label=_("Username or e-mail"), max_length=30, widget=forms.TextInput({'class':'text'}),)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput({'class':'text', 'render_value':False,}), )
    remember = forms.BooleanField(label=_("Remember Me"), help_text=_("If checked you will stay logged in for 3 weeks"), required=False)
    next = forms.CharField(max_length=200, required=False, widget=forms.HiddenInput())
    reason = forms.CharField(max_length=200, required=False, widget=forms.HiddenInput())
    
    user = None

    def clean(self):
        if self._errors:
            return

        user = authenticate(username=self.cleaned_data["username"], password=self.cleaned_data["password"])
        if user:
            if user.is_active:
                self.user = user
            else:
                raise forms.ValidationError(_("This account is currently inactive."))
        else:
            raise forms.ValidationError(_("The username and/or password you specified are not correct."))
    
        return self.cleaned_data

    def login(self, request):
        if self.is_valid():
            auth_login(request, self.user)
            request.user.message_set.create(message=ugettext(u"Successfully logged in as %(username)s.") % {'username': self.user.username})
            if self.cleaned_data['remember']:
                request.session.set_expiry(60 * 60 * 24 * 7 * 3)
            else:
                request.session.set_expiry(0)
            return True
        return False

class OpenIDForm(forms.Form):

    openid_url = forms.CharField(label=_("OpenID Identifier"), max_length=100, widget=forms.TextInput({'class':'text openid'}),)
    next = forms.CharField(max_length=50, required=False, widget=forms.HiddenInput())
    reason = forms.CharField(max_length=50, required=False, widget=forms.HiddenInput())

from film20.emailconfirmation.models import EmailConfirmation

class BaseSignupForm(forms.Form, CleanUsernameMixIn):
    username = forms.CharField(label=_("Username"), max_length=30, widget=forms.TextInput({'class':'text'}))
    inform_friends = forms.BooleanField(label=_("Inform my friends"), required=False)

    def __init__(self, *args, **kw):
        self.request = kw.pop('request', None)
        initial = kw.setdefault('initial', {})
        initial['inform_friends'] = True
        ec = self.get_email_confirmation()
        if ec:
            initial['email'] = ec.email_address.email
        super(BaseSignupForm, self).__init__(*args, **kw)

    def get_email_confirmation(self):
        if self.request:
            tmp_username = self._tmp_username()
            confirmation_key = self.request.GET.get('confirmation_key')
            if tmp_username and confirmation_key:
                ec = EmailConfirmation.objects.filter(confirmation_key=confirmation_key)
                return ec and ec[0] or None

    def _tmp_username(self):
        if self.request:
            return self.request.GET.get('tmp_user')

    def save(self, *args, **kw):
        email_confirmed = False
        username = self.cleaned_data["username"]
        email = self.cleaned_data.get("email") or ""
        password = self.cleaned_data.get("password1")

        tmp_username = self._tmp_username()
        if not tmp_username and self.request and self.request.unique_user.id:
            tmp_username = self.request.unique_user.username

        if tmp_username:
            match = re.match('(\w{3})-[0-9a-f]{20,26}$', tmp_username)
            match = match or re.match('(fb)-\d+', tmp_username)
            assert match
            # rename anonymouse user
            user = User.objects.get(username=tmp_username, is_active=False)
            user.is_active = True
            user.username = username
            user.email = email

            if password:
                user.set_password(password)
            user.save()

            profile = user.get_profile()
            profile.user=user
            profile.registration_source = match.group(1)

            profile.save()
            # update username in activities
            for activity in UserActivity.objects.filter(user=user):
                activity.username = user.username
                activity.save()

            if settings.RECOMMENDATIONS_ENGINE == 'film20.new_recommendations.recommendations_engine' and \
                    Rating.get_user_ratings(user) > settings.RECOMMENDATIONS_MIN_VOTES_USER:
                # recompute recommendations
                from film20.recommendations import engine
                engine.compute_user_features(user, True)
            
            ec = self.get_email_confirmation()
            if ec and ec.email_address.email == email:
                EmailConfirmation.objects.confirm_email(self.request.GET.get('confirmation_key'))
                email_confirmed = True

        else:
            # User.objects.create_user(username, email, **extra)
            user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'email':email},
                    )
            if created:
                if password:
                    user.set_password(password)
                    user.save()
            else:
                # user already exists, probably double form submission
                return user
        
        if email and not email_confirmed:
            add_email(user, email)

        defaults = {}
        if self.request and self.request.geo:
            latitude = self.request.geo.get('latitude')
            longitude = self.request.geo.get('longitude')
            country_code = self.request.geo.get('country_code')
            timezone = self.request.geo.get('timezone')

            if latitude and longitude:
                defaults['latitude'] = str(latitude)
                defaults['longitude'] = str(longitude)

            defaults['country'] = country_code
            defaults['timezone_id'] = timezone

        profile, created = Profile.objects.get_or_create(
            user=user,
            defaults=defaults,
        )
        if not created:
            profile.__dict__.update(defaults)
            profile.save()
        
        from film20.notification import models as notification
        from film20.notification.models import NoticeType

        inform_friends = self.cleaned_data.get('inform_friends')
        if not inform_friends:
            # disable all USER_ACTIVITY notifications
            notice_types = NoticeType.objects.filter(type=NoticeType.TYPE_USER_ACTIVITY)
            for notice_type in notice_types:
                for medium in notification.NOTICE_MEDIA:
                    if medium.supports(notice_type):
                        medium.update_notification_setting(user, notice_type, False)

        if self.request.is_mobile:
            names=dict( (v, k) for k, v in settings.USER_AGENTS )
            platform_name = names.get(self.request.platform, '')
            link = reverse('mobile_app')
            picture = None
        else:
            platform_name = ''
            link = reverse('main_page')
            picture = "/static/layout/logo.png"

        notification.send( [ user ], "useractivity_just_joined", { 
            "user": user,
            "is_mobile": self.request.is_mobile,
            "platform": self.request.platform,
            "platform_name": platform_name,
            "link": link,
            "picture": picture,
        }, delay=30 )
        
        return user

class SignupForm(BaseSignupForm, CleanEmailMixIn):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput({'class':'text'},render_value=False))
    password2 = forms.CharField(label=_("Password (again)"), widget=forms.PasswordInput({'class':'text'},render_value=False))
    email = forms.EmailField(label=_("Email"), widget=forms.TextInput({'class':'text'}))
    confirmation_key = forms.CharField(max_length=40, required=False, widget=forms.HiddenInput())
    
    recaptcha = ReCaptchaField()

    def clean(self):
        if self.request.is_mobile and 'recaptcha' in self._errors:
            del self._errors['recaptcha']
            self.cleaned_data['recaptcha'] = ''
        return self.cleaned_data
            
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("Type the same password twice."))
        return self.cleaned_data['password2']

class UserForm(forms.Form):

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(UserForm, self).__init__(*args, **kwargs)

class AddEmailForm(UserForm, CleanEmailMixIn):

    email = forms.EmailField(label=_("Email"), required=True, widget=forms.TextInput(attrs={'size':'30'}))

    def save(self):
        add_email(self.user, self.cleaned_data["email"])

class ResetPasswordForm(forms.Form):

    # accepts login too
    email = forms.CharField(label=_("Login or Email"), required=True, widget=forms.TextInput(attrs={'class':'text', 'size':'30'}))

    # in case of login, return associated email
    def clean_email(self):
        email = self.cleaned_data['email']
        if '@' in email:
            from django.core.validators import validate_email
            validate_email(email)
            try:
                User.objects.get(email__iexact=email)
                return email
            except User.DoesNotExist, e:
                raise forms.ValidationError(_("Unknown email address, make sure it is correct."))
        else:
            # login entered
            from film20.core.validators import validate_login
            validate_login(email)
            try:
                user = User.objects.get(username__iexact=email)
                if not user.email:
                    raise forms.ValidationError(_("User %s has no email address set") % user.username)
                return user.email
            except User.DoesNotExist, e:
                raise forms.ValidationError(_("Unknown login, make sure it is correct."))

    def save(self):
        email = self.cleaned_data['email']
        for user in User.objects.filter(email__iexact=email):
            new_password = User.objects.make_random_password()
            user.set_password(new_password)
            user.save()
            subject = _("Password reset")
            message = render_to_string("account/password_reset_message.txt", {
                "user": user,
                "new_password": new_password,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        return email

alnum_re = re.compile(r'^\w+$')

class SSORegistrationForm(BaseSignupForm, CleanEmailMixIn):
    email = forms.EmailField(label="Email", required=True, widget=forms.TextInput())
    next = forms.CharField(max_length=512, required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kw):
        from film20.utils.texts import deogonkify
        initial = kw.get('initial')
        if initial and 'username' in initial:
            initial['username'] = clean_username(initial['username'])
        super(SSORegistrationForm, self).__init__(*args, **kw)
