import os
import shutil
import urllib
import mimetypes
from distutils.dir_util import mkpath

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.db.models.signals import post_delete
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import SimpleUploadedFile

from film20.demots import Demotivator
from film20.utils.db import LangQuerySet
from film20.core.urlresolvers import reverse
from film20.facebook_connect.models import LikeCounter


def get_address():
    return "www.%s" % settings.DOMAIN

def get_image_path( instance, filename ):
    return 'img/demots-img/%s/%s' % (filename[0], filename)

def get_demot_path( instance, filename ):
    return 'img/demots/%s/%s' % ( instance.pk, "demot.png" )

THUMBNAIL_SIZE = getattr( settings, 'DEMOT_THUMBNAIL_SIZE', ( 220, 350 ) )


class DemotQuerySet( LangQuerySet ):
    pass

class Demot( models.Model ):

    LANG = models.CharField( max_length=2, default=settings.LANGUAGE_CODE )

    line1 = models.CharField( _( "Line 1" ), max_length=150 )
    line2 = models.CharField( _( "Line 2" ), max_length=255, null=True, blank=True )

    user = models.ForeignKey( User, verbose_name=_( "User", related_name = "demots" ) )
    
    created_at = models.DateTimeField( _( "Created at" ), auto_now_add=True )
    based_on = models.ForeignKey( 'self', verbose_name=_( 'Based on' ), null=True, blank=True )

    image_url = models.URLField( _( "Image url" ), null=True, blank=True )
    image = models.ImageField( _( "Image" ), max_length=255, null=True, blank=True, upload_to=get_image_path )

    # generated demot
    final_image = models.ImageField( _( "Demot Image" ), max_length=255, null=True, blank=True, upload_to=get_demot_path, editable=False )
    
    like_counter = generic.GenericRelation( LikeCounter )

    objects = DemotQuerySet()

    class Meta:
        ordering = [ "-created_at", ]
        verbose_name = _( "Demot" )
        verbose_name_plural = _( "Demots" )
        unique_together = ( 'LANG', 'user', 'line1', 'line2' )

    def __unicode__( self ):
        return self.line1

    def get_absolute_url( self ):
        from film20.useractivity.models import UserActivity
        self._act_id = getattr( self, '_act_id', UserActivity.objects.get( demot=self ).pk )
        return reverse( 'show_demot', args=[ self.user, self._act_id ] )

    @property
    def likes( self ):
        return sum( [ l.likes for l in self.like_counter.all() ] )

    @property
    def demot_directory( self, create=True ):
        directory = os.path.join( settings.MEDIA_ROOT, "img/demots/%s" % self.pk )
        if create and not os.path.exists( directory ):
            mkpath( directory )
        return directory
    
    @property
    def demot_path( self ):
        path = os.path.join( self.demot_directory, "demot.png" )
        return { 'path': path, 'url': path.replace( settings.MEDIA_ROOT, settings.MEDIA_URL ) }

    def get_thumbnail( self, size=THUMBNAIL_SIZE ):
        path = os.path.join( self.demot_directory, "thumb-%sx%s.png" % ( size[0], size[1] ) )
        if not os.path.exists( path ):
            demotivator = Demotivator( self.image.path, self.line1, self.line2, get_address() )
            demotivator.get_thumbnail( path, size )
        return { 'path': path, 'url': path.replace( settings.MEDIA_ROOT, settings.MEDIA_URL ) }

    def remove_thumbnail( self, size=THUMBNAIL_SIZE ):
        path = self.get_thumbnail( size )['path']
        if os.path.exists( path ):
            os.remove( path )

    def save( self, force_insert=False, force_update=False, using=None ):
        if not self.image and self.image_url:
            filename, headers = urllib.urlretrieve( self.image_url.encode( 'utf-8' ) )
            type = headers.get( 'Content-Type' )
            if not type or not mimetypes.guess_all_extensions( type ):
                raise ValidationError( 'Broken image' )

            self.image = SimpleUploadedFile( filename, open( filename ).read(), content_type = type )
            self.image_url = None

        super( Demot, self ).save( force_insert, force_update, using )
        
        # generate demot
        if self.image and not self.final_image:
            demotivator = Demotivator( self.image, self.line1, self.line2, get_address() )
            demotivator.create( self.demot_path['path'] )
            
            # generate default thumbnail
            self.get_thumbnail()
            
            self.final_image = self.demot_path['url']
            self.save()
        
            # create/update activity
            self.save_activity()

    def save_activity( self ):
        from film20.useractivity.models import UserActivity
        
        defaults = dict(
            user = self.user,
            object_title = self.line1,
            username = self.user.username,
            LANG = settings.LANGUAGE_CODE,
            content = self.get_thumbnail()['url'],
            activity_type = UserActivity.TYPE_DEMOT,
            title = "%s %s" % ( _( "added a demot" ), self.line1 ),
        )
        act, created = UserActivity.objects.get_or_create( demot=self, defaults=defaults)
        if not created:
            for (k, v) in defaults.items():
                setattr(act, k, v)
            act.save()

    def delete( self ):
        for demot in Demot.objects.filter( based_on=self ):
            demot.based_on = None
            demot.save()

        super( Demot, self ).delete()

    @classmethod
    def clear_directory( cls, sender, instance, *args, **kwargs ):
        if os.path.exists( instance.demot_directory ):
            shutil.rmtree( instance.demot_directory )


post_delete.connect( Demot.clear_directory, sender=Demot )
