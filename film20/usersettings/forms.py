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
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib.auth.models import User
import mimetypes, urllib
from film20.core.models import Profile

class LocationForm(forms.ModelForm):
    """
    Profile location form
    """

    class Meta:
        model = Profile
        fields = ('location', 'latitude', 'longitude', 'country')

class UserForm(forms.Form):
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(UserForm, self).__init__(*args, **kwargs)

class ChangePasswordForm(UserForm):

    oldpassword = forms.CharField(label=_("Current Password"), widget=forms.PasswordInput({'class':'text', 'render_value':False,}), )
    password1 = forms.CharField(label=_("New Password"), widget=forms.PasswordInput({'class':'text', 'render_value':False,}), )
    password2 = forms.CharField(label=_("New Password (again)"), widget=forms.PasswordInput({'class':'text', 'render_value':False,}), )

    def clean_oldpassword(self):
        if not self.user.check_password(self.cleaned_data.get("oldpassword")):
            raise forms.ValidationError(_("Please type your current password."))
        return self.cleaned_data["oldpassword"]

    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]

    def save(self):
        self.user.set_password(self.cleaned_data['password1'])
        self.user.save()

class SetPasswordForm(UserForm):

    password1 = forms.CharField(label=_("New Password"), widget=forms.PasswordInput({'class':'text', 'render_value':False,}), )
    password2 = forms.CharField(label=_("New Password (again)"), widget=forms.PasswordInput({'class':'text', 'render_value':False,}), )

    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password1"]

    def save(self):
        self.user.set_password(self.cleaned_data['password1'])
        self.user.save()

class ProfileForm(forms.ModelForm):
    """
    Profile Form. Composed by Profile, User and LocalizedProfile fields
    """
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance.display_name:
            pass
#            self.fields['display_name'].widget.attrs['readonly'] = True

    first_name = forms.CharField(label=_("Name"), required=False)    
    last_name = forms.CharField(label=_("Surname"), required=False)
    email = forms.EmailField(label=_("Email"), required=False)
    
    display_name = forms.CharField(label=_("Display name"), required=False)

    description = forms.CharField(max_length=255, label=_("About you"), widget=forms.Textarea({'class':'textarea'}), required=False)
    blog_title = forms.CharField(max_length=200, label=_("Blog title"), required=False)
    
    phone_number = forms.RegexField(r"^\+?\d{9,}$", max_length=64, label=_("Phone number"), required=False)

    class Meta:
        model = Profile
        fields = (
            'first_name',
            'last_name',
            'email',
            'display_name',
            'gender',
            'description', 
            'website',
            'jabber_id', 
            'gg', 
            'msn', 
            'icq', 
            'aol', 
            'phone_number',
            'criticker_name', 
            'imdb_name',
            'blog_title'
        )

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

    def clean_display_name(self):
        """
        Verify that the display name is unique for user
        """
        display_name  = self.cleaned_data.get("display_name")

        if not display_name:
            return self.instance.user.username
        
        profiles = Profile.objects.filter(Q(display_name = display_name) | Q(user__username = display_name)).exclude(user = self.instance.user)
        if len(profiles) > 0:
            raise forms.ValidationError(_("This display name is already used."))
        else:
            return display_name

from piston.models import Consumer

class ConsumerForm(forms.ModelForm):
    class Meta:
        model = Consumer
        fields = ('name', 'description')

from django.forms import MultipleChoiceField, CheckboxSelectMultiple

class TVChannelsForm(forms.Form):
    channels = MultipleChoiceField(required=False, widget=CheckboxSelectMultiple())

from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import SimpleUploadedFile

class AvatarForm( forms.Form ):
    """
    The avatar form requires only one image field.
    """
    photo = forms.ImageField( label=_( 'Add your avatar. Upload new file with a photo' ), required=False, help_text=_( 'JPG, PNG, GIF - Max: 5MB' ) )
    url = forms.URLField( label=_( 'or use an image from the web' ), required=False )
    url.widget.attrs['style'] = 'display: none'


    def clean_url( self ):
        url = self.cleaned_data.get( 'url' )
        if not url: 
            return ''
        
        filename, headers = urllib.urlretrieve( url )
        if not mimetypes.guess_all_extensions( headers.get( 'Content-Type' ) ):
            raise forms.ValidationError( _( 'The file type is invalid: %s' % type ) )

        return SimpleUploadedFile( filename, open( filename ).read(), content_type=headers.get( 'Content-Type' ) )

    def clean( self ):
        image = self.cleaned_data.get( 'photo' ) or self.cleaned_data.get( 'url' )
        if not image:
            raise forms.ValidationError( _( 'You must enter one of the options' ) )

        w, h = get_image_dimensions( image )

        min_w, min_h, thumb_w, thumb_h = 96, 96, 480, 480

        if w > thumb_w: h = max( h * thumb_w / w, 1 ); w = thumb_w
        if h > thumb_h: w = max( w * thumb_h / h, 1 ); h = thumb_h

        if w < min_w or h < min_h:
            raise forms.ValidationError( _( "You must select a image with a minimum of 96x96 pixels." ) )
        return self.cleaned_data

class AvatarCropForm( forms.Form ):
    """
    Crop dimensions form
    """
    top = forms.IntegerField()
    bottom = forms.IntegerField()
    left = forms.IntegerField()
    right = forms.IntegerField()

    def clean( self ):
        if int( self.cleaned_data.get( 'right' ) ) - int( self.cleaned_data.get( 'left' ) ) < 96:
            raise forms.ValidationError( _( "You must select a portion of the image with a minimum of 96x96 pixels." ) )
        else:
            return self.cleaned_data


from django.forms.widgets import Widget
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from film20.useractivity.models import UserActivity

class ActivitiesWidget( Widget ):
    def __init__( self, attrs=None ):
        super( ActivitiesWidget, self ).__init__( attrs )
        self.choices = UserActivity.ACTIVITY_TYPE_CHOICES
    
    def decompress( self, value ):
        return value.split( ',' )
    
    def render( self, name, value, attrs=None ):
        if value is None:
            value = ''
        output = []
        selected = self.decompress( value )
        has_id = attrs and 'id' in attrs
        for i, choice in enumerate( self.choices ):
            v, l = choice
            final_attrs = self.build_attrs( attrs, type='checkbox', name=name )
            final_attrs['value'] = force_unicode( v )
            if str( v ) in selected:
                final_attrs['checked'] = 'checked'
            if has_id:
                final_attrs['id'] = '%s_%s' % ( attrs['id'], i )
            output.append( u'<input%s /> %s' % ( flatatt( final_attrs ), l ) )
        return mark_safe( '<div class="activities_to_select">%s</div>' % ''.join( [ '<p>%s<p/>' % i for i in output ] ) )
    
    def value_from_datadict( self, data, files, name ):
        if not data.has_key( name ): 
            return ''
        values = data.getlist( name )
        return ','.join( values ) if values else ''


class CustomFilterForm( forms.Form ):
    activities_on_dashboard = forms.CharField( label=_( "Select Activities" ), widget=ActivitiesWidget )
    custom_filter = forms.BooleanField( label=_( "Use custom dashboard" ), required=False )
