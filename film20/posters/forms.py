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

import mimetypes, urllib

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import SimpleUploadedFile

from film20.posters.models import POSTER_MIN_DIMENSION

class UploadedImageForm( forms.Form ):
    uploaded_image = forms.IntegerField( required = True )
    in_all_languages = forms.BooleanField( required = False )
    is_main = forms.BooleanField( required = False )

class PhotoForm( forms.Form ):
    """
    The film poster form requires only one image field.
    """
    photo = forms.ImageField( required = False )
    url = forms.URLField( required = False )

    def clean_url( self ):
        url = self.cleaned_data.get( 'url' )
        if not url: return ''
        filename, headers = urllib.urlretrieve( url )
        type = headers.get( 'Content-Type' )
        if not type or not mimetypes.guess_all_extensions( type ):
            raise forms.ValidationError( _( 'The file type is invalid: %s' % type ) )
        return SimpleUploadedFile( filename, open( filename ).read(), content_type = headers.get( 'Content-Type' ) )

    def clean( self ):
        image = self.cleaned_data.get( 'photo' ) or self.cleaned_data.get( 'url' )
        if not image:
            raise forms.ValidationError( _( 'You must enter one of the options' ) )
        
        min_w, min_h = POSTER_MIN_DIMENSION

        # fix for FLM-609
        dimension = get_image_dimensions( image )
        if dimension is None: w, h = 0, 0
        else: 
            w, h = dimension

        if w < min_w or h < min_h:
            raise forms.ValidationError( 
                _( "You must select a image with a minimum of %(width)dx%(height)d pixels." % { 'width': min_w, 'height': min_h } )
            )

        return self.cleaned_data
