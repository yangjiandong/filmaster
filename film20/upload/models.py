from os import path

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import filesizeformat

def get_upload_path( instance, filename ):
    if len( filename ) > 60:
        basename, extension = path.splitext( filename )
        filename = "%s%s" % ( filename[:50], extension )

    return "uploads/%s/%s" % ( filename[0], filename )

class UploadedImage( models.Model ):
    image = models.ImageField( _( "Image" ), upload_to=get_upload_path )
    uploaded_at = models.DateTimeField( _( "Uploaded at" ), auto_now_add=True )

    class Meta:
        abstract = True

    def __unicode__( self ):
        return u"%s" % ( self.image )
    
    @property
    def size( self ):
        return filesizeformat( self.file.size )

class UserUploadedImage( UploadedImage ):
    uploaded_by = models.ForeignKey( User, verbose_name=_( "Uploaded by" ) )
    
    class Meta( UploadedImage.Meta ):
        verbose_name = _( "User uploaded image" )
