import os, shutil, math, operator
try:
    from PIL import Image
except:
    import Image

from django.conf import settings
from film20.utils.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from film20.userprofile.models import Avatar
from film20.utils.avatars import get_avatar_path

DEFAULT_AVATAR = getattr(settings, "DEFAULT_AVATAR", os.path.join(settings.MEDIA_ROOT, "img/avatars/generic.jpg"))

# FLM-647
class AvatarTestCase( TestCase ):

    def setUp( self ):
        self.client = Client( follow=True )

        # test user 
        self.u = User.objects.create_user( "user", "user@user.com", "user" )
        self.u.is_superuser = True
        self.u.save()

        # turn on caching
        self.old_settings = settings.CACHE_AVATARS
        settings.CACHE_AVATARS = True

        self.image = open( os.path.join( os.path.dirname( __file__ ), "test_media/test_avatar.jpg" ) )
        self.image2 = open( os.path.join( os.path.dirname( __file__ ), "test_media/test_avatar2.jpg" ) )
        self.tmp_file = "/tmp/temp_image.jpg"

    def tearDown( self ):
        User.objects.all().delete()
        Avatar.objects.all().delete()
        
        # revert cache settings
        settings.CACHE_AVATARS = self.old_settings

        self.image.close()
        self.image2.close()

        if os.path.exists( self.tmp_file ):
            os.remove( self.tmp_file )

    def test_avatar_caching( self ):
        # 1. add first avatar
        self.client.login( username='user', password='user' )
        self.assertEqual( get_avatar_path( self.u, 72 ), self._to_media_url( DEFAULT_AVATAR, 72 ) )
        
        self.client.post( reverse( 'edit_avatar' ), { "photo": self.image } )
        self.client.post( reverse( 'crop_avatar' ), { "top": 1, "left": 1, "bottom": 100, "right": 100 } )

        avatar = Avatar.objects.get( user=self.u, valid=True )
        self.assertEqual( get_avatar_path( self.u, 72 ), self._to_media_url( avatar.image.url, 72 ) )

        shutil.copy( avatar.image.path, self.tmp_file )

        # 2. replace avatar
        self.client.post( reverse( 'edit_avatar' ), { "photo": self.image2 } )
        self.client.post( reverse( 'crop_avatar' ), { "top": 1, "left": 1, "bottom": 100, "right": 100 } )

        avatar = Avatar.objects.get( user=self.u, valid=True )
        self.assertEqual( get_avatar_path( self.u, 72 ), self._to_media_url( avatar.image.url, 72 ) )

        rms = self._compare_images( self.tmp_file, avatar.image.path )
        self.assertTrue( rms > 0.0 )

        # 3. remove avatar
        Avatar.objects.get( user=self.u ).delete()
        self.assertEqual( get_avatar_path( self.u, 72 ), self._to_media_url( DEFAULT_AVATAR, 72 ) )

    def test_no_avatar_in_storage( self ):
        self.client.login( username='user', password='user' )
        self.client.post( reverse( 'edit_avatar' ), { "photo": self.image } )
        self.client.post( reverse( 'crop_avatar' ), { "top": 1, "left": 1, "bottom": 100, "right": 100 } )

        avatar = Avatar.objects.get( user=self.u, valid=True )
        self.assertEqual( get_avatar_path( self.u, 72 ), self._to_media_url( avatar.image.url, 72 ) )

        os.remove( avatar.image.path )
        os.remove( os.path.join( settings.MEDIA_ROOT, self._to_media_url( avatar.image.name, 72 ) ) )
        self.assertEqual( get_avatar_path( self.u, 72 ), self._to_media_url( DEFAULT_AVATAR, 72 ) )


    def _to_media_url( self, url, size ):
        path, ext = os.path.splitext( url )
        thumb_path = "%s.%s%s" % ( path, size, ext )
        return thumb_path.replace( settings.MEDIA_ROOT, settings.MEDIA_URL )

    def _compare_images( self, image1, image2 ):
        h1 = Image.open( image1 ).histogram()
        h2 = Image.open( image2 ).histogram()

        return math.sqrt(reduce(operator.add, map(lambda a,b: (a-b)**2, h1, h2))/len(h1))

