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

import os

from django.test import Client
from film20.utils.test import TestCase
from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.core.files.images import get_image_dimensions
from django.conf import settings
from film20.core.models import Film
from film20.posters.models import ModeratedPhoto

class FilmPostersTestCase( TestCase ):
    def setUp( self ):
        self.client = Client( follow=True )
        
        self.user = User.objects.create_user( "user", "user@user.com", "user" )
        
        self.mod = User.objects.create_user( "mod", "mod@mod.com", "mod" )
        self.mod.user_permissions.add( Permission.objects.get( codename="can_accept_posters" ) )
        self.mod.save()

        self.film = Film( type=1, imdb_code="199123", release_year=2008, 
                       title="The Incredible Hulk", permalink="the_incredible_hulk" )
        self.film.save()

        self.image = open( os.path.join( os.path.dirname( __file__ ), "images/test.jpg" ) )

    def tearDown( self ):
#        Film.objects.all().delete()
#        User.objects.all().delete()
        
        self.image.close()

    def testUploadingWithResizing( self ):
        
        self.client.login( username='user', password='user' )
        response = self.client.post( reverse( 'add-poster', args=[self.film.permalink] ), { "photo": self.image })

        for poster in ModeratedPhoto.objects.get_by_object( self.film ):
            w, h = get_image_dimensions( poster.image )
            dim = settings.POSTER_DIMENSION
            self.assertTrue( w <= dim[0], h <= dim[1])
            

    def testAutomaticallyAccept( self ):
        
        self.client.login( username='mod', password='mod' )
        response = self.client.post( reverse( 'add-poster', args=[self.film.permalink] ), { "photo": self.image })
        
        poster = ModeratedPhoto.objects.get_by_object( self.film )[0]
        film = Film.objects.get( pk=self.film.pk )
        
        self.assertEqual( poster.moderation_status, ModeratedPhoto.STATUS_ACCEPTED )
        self.assertTrue( film.image is not None )

#
#    TODO:
#       Uncomment when moderation panel will be enabled   
# 
#    def testReject( self ):
#
#        from django.core import mail
#
#        mail.outbox = []
#
#        self.client.login( username='user', password='user' )
#        response = self.client.post( reverse( 'add-poster', args=[self.film.permalink] ), { "photo": self.image })
#
#        poster = ModeratedPhoto.objects.get_by_object( self.film )[0]
#        ps_film = Film.objects.get( pk=self.film.pk )
#
#        reason = "Broken file."
#        self.client.login( username='mod', password='mod' )
#        response = self.client.post( reverse( 'poster-admin' ), { "id": poster.id, "reject": "1", "confirmed": "1", "reason": reason })
#       
#        poster = ModeratedPhoto.objects.get_by_object( self.film )[0]
#        film = Film.objects.get( pk=self.film.pk )
#
#        self.assertEqual( poster.moderation_status, ModeratedPhoto.STATUS_REJECTED )
#        self.assertEqual( poster.rejection_reason, reason )
#        self.assertEqual( film.image, ps_film.image )
#
#
#        self.assertEqual( len( mail.outbox ), 1 )
#
#        print mail.outbox[0].body
#
#        self.assertTrue( reason in mail.outbox[0].body )

    def testRegularUserAdd( self ):
       
        self.client.login( username='user', password='user' )
        response = self.client.post( reverse( 'add-poster', args=[self.film.permalink] ), { "photo": self.image })
        
        poster = ModeratedPhoto.objects.get_by_object( self.film )[0]
        film = Film.objects.get( pk=self.film.pk )
        
        self.assertEqual( poster.moderation_status, ModeratedPhoto.STATUS_UNKNOWN )


    def testPhotoUpload( self ):
        self.client.login( username='mod', password='mod' )

        for e in [ 'png', 'jpg', 'bmp', 'gif' ]:
            image = open( os.path.join( os.path.dirname( __file__ ), "images/test.%s" % e ) )
            response = self.client.post( reverse( 'add-poster', args=[self.film.permalink] ), { "photo": image })
            image.close()
        
            poster = ModeratedPhoto.objects.get_by_object( self.film )[0]
            film = Film.objects.get( pk=self.film.pk )
        
            self.assertEqual( poster.moderation_status, ModeratedPhoto.STATUS_ACCEPTED )
            self.assertTrue( film.image is not None )

