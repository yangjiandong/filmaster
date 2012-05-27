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

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from film20.moderation.registry import registry, AlreadyRegistered
from film20.moderation.models import ModeratedObject
from film20.moderation.items import ModeratedItem, ModeratedObjectItem, ModerationException

from film20.moderation.tests.base import BaseTest
from film20.moderation.tests.models import ModeratedItem1, TestModeratedObject

class ModeratedItemTest( BaseTest ):
   
    def testNames( self ):
        self.assertEquals( self.i1.get_name(), 'user-test' )

    def testNotImplementedMethods( self ):
        
        self.assertRaises( NotImplementedError, self.i1.get_queryset, ModeratedObject.STATUS_UNKNOWN )
        self.assertRaises( NotImplementedError, self.i1.get_not_moderated )
        self.assertRaises( NotImplementedError, self.i1.accept_item, None, None )
        self.assertRaises( NotImplementedError, self.i1.reject_item, None, None )

    def testPermissions( self ):
        self.assertFalse( self.i1.can_accept( None, self.u1 ) )
        self.assertTrue( self.i1.can_accept( None, self.u2 ) )

        self.assertFalse( self.i1.can_reject( None, self.u1 ) )
        self.assertTrue( self.i1.can_reject( None, self.u2 ) )
    
    def testRegistry( self ):
        self.assertRaises( AttributeError, registry.register, User )
        self.assertRaises( AttributeError, registry.register, User() )

        self.assertEqual( registry.get_by_name( 'test-moderated-object' ).get_name(),
                         'test-moderated-object' )
    
    def testModeratedObject( self ):
        self.assertEqual( self.tm1.moderation_status, TestModeratedObject.STATUS_UNKNOWN )

        self.tm1.accept( self.u1 )
        self.assertEqual( self.tm1.moderation_status, TestModeratedObject.STATUS_ACCEPTED )
        self.assertEqual( self.tm1.moderation_status_by, self.u1 )
        self.assertTrue( self.tm1.moderation_status_at is not None )

        reason = "Ble, ble, bla, bla."
        self.tm2.reject( self.u2, reason )
        self.assertEqual( self.tm2.moderation_status, TestModeratedObject.STATUS_REJECTED )
        self.assertEqual( self.tm2.moderation_status_by, self.u2 )
        self.assertEqual( self.tm2.rejection_reason, reason )
        self.assertTrue( self.tm2.moderation_status_at is not None )
