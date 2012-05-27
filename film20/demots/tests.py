import os

from django.core.files import File
from django.conf import settings
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.core.files.images import get_image_dimensions

from film20.demots.models import Demot

class DemotsTestCase( TestCase ):

    def setUp( self ):
        self.user = User.objects.create_user( "user", "user@user.com", "user" )
        self.image = os.path.join( os.path.dirname( __file__ ), "resources/images/test.jpg" )
        self.image_file = File( open( self.image, 'r' ) )

    def tearDown( self ):
        User.objects.all().delete()
        Demot.objects.all().delete()

    def test_create_and_delete( self ):
        demot = Demot( pk=-1, user=self.user, line1='Line 1 bla bla bla', line2='Line 2 bla bla bla' )
        demot.image.save( 'img-1.png', self.image_file )
        demot.save() 

        self.assertTrue( demot.final_image is not None )

        demot_path = demot.demot_path['path']
        demot_directory = demot.demot_directory

        self.assertTrue( os.path.exists( demot_path ) )
        self.assertTrue( os.path.exists( demot_directory ) )

        demot.delete()

        self.assertFalse( os.path.exists( demot_path ) )
        self.assertFalse( os.path.exists( demot_directory ) )
