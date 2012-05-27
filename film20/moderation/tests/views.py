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

from django.test import Client
from django.core.urlresolvers import reverse

from film20.moderation.registry import registry
from film20.moderation.tests.base import BaseTest
from film20.moderation.tests.models import ModeratedItem1, TestModeratedObject

class ViewsTest( BaseTest ):
    
    def setUp( self ):
        super( ViewsTest, self ).setUp()
        # ..
        self.client = Client( follow=True )
        self.mi = registry.get_by_name( 'test-moderated-object' )


    def testNoLoginAccess( self ):

        self.client.login( username='user', password='user' )
        response = self.client.get( reverse( 'moderation' ) )
        self.assertEqual( response.status_code, 200 )
        
        self.client.logout()
        response = self.client.get( reverse( 'moderation' ) )
        self.assertEqual( response.status_code, 302 )
    
    def testAcceptRejectWithPermissions( self ):
        
        self.client.login( username='root', password='root' )
        response = self.client.post( reverse( 'moderate-item', args=[ self.mi.get_name() ] ), { "id": self.tm1.id, "accept": "1" })
        self.tm1 = TestModeratedObject.objects.get( pk=self.tm1.pk )
        self.assertEqual( self.tm1.moderation_status, TestModeratedObject.STATUS_ACCEPTED )
        self.assertEqual( self.tm1.moderation_status_by, self.u2 )

        reason = "Ble, ble, bla, bla."
        self.client.login( username='root', password='root' )
        response = self.client.post( reverse( 'moderate-item', args=[ self.mi.get_name() ] ), { "id": self.tm1.id, "reject": "1", "confirmed": "1", "reason": reason })
        self.tm1 = TestModeratedObject.objects.get( pk=self.tm1.pk )
        self.assertEqual( self.tm1.moderation_status, TestModeratedObject.STATUS_REJECTED )
        self.assertEqual( self.tm1.moderation_status_by, self.u2 )
        self.assertEqual( self.tm1.rejection_reason, reason )

    def testAcceptRejectWithoutPermissions( self ):
        
        self.client.login( username='user', password='user' )
        response = self.client.post( reverse( 'moderate-item', args=[ self.mi.get_name() ] ), { "id": self.tm1.id, "accept": "1" })
        self.tm1 = TestModeratedObject.objects.get( pk=self.tm1.pk )
        self.assertEqual( self.tm1.moderation_status, TestModeratedObject.STATUS_UNKNOWN )
        self.assertTrue( self.tm1.moderation_status_by is None )
        self.assertTrue( self.tm1.moderation_status_at is None )

        self.client.login( username='user', password='user' )
        response = self.client.post( reverse( 'moderate-item', args=[ self.mi.get_name() ] ), { "id": self.tm1.id, "reject": "1", "confirmed": "1", "reason": "Ble, ble, bla, bla." })
        self.tm1 = TestModeratedObject.objects.get( pk=self.tm1.pk )
        self.assertEqual( self.tm1.moderation_status, TestModeratedObject.STATUS_UNKNOWN )
        self.assertTrue( self.tm1.moderation_status_by is None )       
        self.assertTrue( self.tm1.moderation_status_at is None )
        self.assertTrue( self.tm1.rejection_reason is None )

    def testRssFeed( self ):

        self.client.login( username='user', password='user' )
        response = self.client.get( reverse( 'moderated-item-rss', args=[ self.mi.get_name() ] ) )
        self.assertEqual( response.status_code, 200 )
    
    def testModeratedItemNotExist( self ):
        self.client.login( username='root', password='root' )
        response = self.client.get( reverse( 'moderate-item', args=[ self.mi.get_name() ] ) )
        self.assertEqual( response.status_code, 200 )
        
        response = self.client.get( reverse( 'moderate-item', args=[ "fake-moderated-item" ] ) )
        self.assertEqual( response.status_code, 404 )


