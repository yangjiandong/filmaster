import mimetypes, urllib

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.files.images import get_image_dimensions
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import UserUploadedImage

# TODO settings
THUMBNAIL_DIMENSION = ( 61, 102 )

class UserUploadImageForm( forms.ModelForm ):

    image = forms.ImageField( required = False )
    url = forms.URLField( required = False )

    class Meta:
        model = UserUploadedImage
        fields = ( 'image', )

    def clean_url( self ):
        url = self.cleaned_data.get( 'url' )
        if not url: 
            return ''

        filename, headers = urllib.urlretrieve( url )
        type = headers.get( 'Content-Type' )
        if not type or not mimetypes.guess_all_extensions( type ):
            raise forms.ValidationError( _( 'The file type is invalid: %s' % type ) )

        return SimpleUploadedFile( filename, open( filename ).read(), content_type = headers.get( 'Content-Type' ) )

    def clean( self ):
        image = self.cleaned_data.get( 'image' ) or self.cleaned_data.get( 'url' )
        if not image:
            raise forms.ValidationError( _( 'You must enter one of the options' ) )
        
        self.cleaned_data['image'] = image

        min_w, min_h = THUMBNAIL_DIMENSION

        dimension = get_image_dimensions( image )
        if dimension is None: w, h = 0, 0
        else: 
            w, h = dimension

        if w < min_w or h < min_h:
            raise forms.ValidationError(
                _( "You must select a image with a minimum of %(width)dx%(height)d pixels." % { 'width': min_w, 'height': min_h } )
            )

        return self.cleaned_data
