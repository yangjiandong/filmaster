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
from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth.models import User
from models import EmailValidation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.images import get_image_dimensions
import mimetypes, urllib
from film20.core.models import LocalizedProfile

if not settings.AUTH_PROFILE_MODULE:
    raise SiteProfileNotAvailable
try:
    app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
    Profile = models.get_model(app_label, model_name)
except (ImportError, ImproperlyConfigured):
    raise SiteProfileNotAvailable

class LocationForm(forms.ModelForm):
    """
    Profile location form
    """

    class Meta:
        model = Profile
        fields = ('location', 'latitude', 'longitude', 'country')

class ProfileForm(forms.ModelForm):
    """
    Profile Form. Composed by all the Profile model fields.
    """
    first_name = forms.CharField(label=_("Name"), required=False)    
    last_name = forms.CharField(label=_("Surname"), required=False)
    email = forms.EmailField(label=_("Email"), required=False)

    description = forms.CharField(max_length=255, label=_("About you"), widget=forms.Textarea({'class':'textarea'}), required=False)
    blog_title = forms.CharField(max_length=200, label=_("Blog title"), required=False)
    
    class Meta:
        model = Profile
        fields = ('first_name', 'last_name', 'email', 'gender', 'website',
                  'jabber_id', 'gg', 'msn', 'icq', 'aol', 'phone_number', 'criticker_name', 'imdb_name',
                  'description', 'blog_title')

    def clean_email(self):
        """
        Verify that the email is unique for user
        """
        email = self.cleaned_data.get("email")

        if not email: return email

        users = User.objects.filter(email=email).exclude(id=self.instance.user.id)
        if len(users) > 0:
            raise forms.ValidationError(_("That e-mail is already used."))
        else:
            return email

class PublicFieldsForm(forms.ModelForm):
    """
    Public Fields of the Profile Form. Composed by all the Profile model fields.
    """
    class Meta:
        model = Profile
        exclude = ('date', 'user', 'public')

class AvatarForm(forms.Form):
    """
    The avatar form requires only one image field.
    """
    photo = forms.ImageField(required=False)
    url = forms.URLField(required=False)

    def clean_url(self):
        url = self.cleaned_data.get('url')
        if not url: return ''
        filename, headers = urllib.urlretrieve(url)
        if not mimetypes.guess_all_extensions(headers.get('Content-Type')):
            raise forms.ValidationError(_('The file type is invalid: %s' % type))
        return SimpleUploadedFile(filename, open(filename).read(), content_type=headers.get('Content-Type'))

    def clean(self):
        image = self.cleaned_data.get('photo') or self.cleaned_data.get('url')
        if not image:
            raise forms.ValidationError(_('You must enter one of the options'))

        w, h = get_image_dimensions( image )

        # TODO: add AVATAR_MIN_SIZE to settings
        min_w, min_h, thumb_w, thumb_h = 96, 96, 480, 480

        if w > thumb_w: h = max( h * thumb_w / w, 1 ); w = thumb_w
        if h > thumb_h: w = max( w * thumb_h / h, 1 ); h = thumb_h

        if w < min_w or h < min_h:
            raise forms.ValidationError(_("You must select a image with a minimum of 96x96 pixels."))
        return self.cleaned_data

class AvatarCropForm(forms.Form):
    """
    Crop dimensions form
    """
    top = forms.IntegerField()
    bottom = forms.IntegerField()
    left = forms.IntegerField()
    right = forms.IntegerField()

    def clean(self):
        if int(self.cleaned_data.get('right')) - int(self.cleaned_data.get('left')) < 96:
            raise forms.ValidationError(_("You must select a portion of the image with a minimum of 96x96 pixels."))
        else:
            return self.cleaned_data

class RegistrationForm(forms.Form):

    username = forms.CharField(max_length=255, min_length = 3, label=_("Username"))
    email = forms.EmailField(required=False, label=_("E-mail address"))
    password1 = forms.CharField(widget=forms.PasswordInput, label=_("Password"))
    password2 = forms.CharField(widget=forms.PasswordInput, label=_("Password (again)"))

    def clean_username(self):
        """
        Verify that the username isn't already registered
        """
        username = self.cleaned_data.get("username")
        if not set(username).issubset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"):
            raise forms.ValidationError(_("That username has invalid characters. The valid values are letters, numbers and underscore."))

        if User.objects.filter(username__iexact=username).count() == 0:
            return username
        else:
            raise forms.ValidationError(_("The username is already registered."))

    def clean(self):
        """
        Verify that the 2 passwords fields are equal
        """
        if self.cleaned_data.get("password1") == self.cleaned_data.get("password2"):
            return self.cleaned_data
        else:
            raise forms.ValidationError(_("The passwords inserted are different."))

    def clean_email(self):
        """
        Verify that the email exists
        """
        email = self.cleaned_data.get("email")

        if not email: return  email

        try:
            User.objects.get(email=email)
            raise forms.ValidationError(_("That e-mail is already used."))
        except User.DoesNotExist:
            try:
                EmailValidation.objects.get(email=email)
                raise forms.ValidationError(_("That e-mail is already being confirmed."))
            except EmailValidation.DoesNotExist:
                return email

class EmailValidationForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        """
        Verify that the email exists
        """
        email = self.cleaned_data.get("email")
        if not (User.objects.filter(email=email) or EmailValidation.objects.filter(email=email)):
            return email

        raise forms.ValidationError(_("That e-mail is already used."))

