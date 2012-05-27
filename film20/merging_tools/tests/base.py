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

from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType

from film20.moderation.models import ModeratedObject
from film20.moderation.tests.models import ModeratedItem1, TestModeratedObject

class BaseTest( TestCase ):
    
    def setUp( self ):
        self.i1 = ModeratedItem1()

        self.tm1 = TestModeratedObject.objects.create()
        self.tm2 = TestModeratedObject.objects.create()
        
        # test user with no permissions
        self.u1 = User.objects.create_user( "user", "user@user.com", "user" )
        
        # test user with moderation_permission
        self.u2 = User.objects.create_user( "root", "root@root.com", "root" )
        self.u2.user_permissions.add( Permission.objects.get( codename="test_moderation_permission" ) )
        self.u2.save()
        

    def tearDown( self ):
        User.objects.all().delete()
        TestModeratedObject.objects.all().delete()
