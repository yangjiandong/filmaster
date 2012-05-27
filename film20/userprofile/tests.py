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

import unittest

from film20.utils.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from film20.core.models import Profile
from film20.userprofile.forms import ProfileForm

class EmailValidationTestCase(TestCase):
    """
        Test if other user is using the same email
    """
    def setUp(self):

        # set up users
        self.u1= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.u1.save()

        self.u2= User.objects.create_user('adz', 'adz@gmail.com', 'secret')
        self.u2.save()

    def tearDown( self ):
        User.objects.all().delete()
        Profile.objects.all().delete()

    def test_new_mail(self):
        """
            User pass new uniqe email
        """
        
        profile = self.u1.get_profile()
        
        test_profile_form = ProfileForm( {'email':'borys.musielak@gmail.com'}, instance=profile )
        test_profile_form.email = 'michukzx@gmail.com'
        
        self.assertTrue( test_profile_form.is_valid() )

    def test_same_mail(self):
        """
            User pass mail existing in db 
        """
        
        profile = self.u1.get_profile()
        
        test_profile_form = ProfileForm( instance=profile )
        test_profile_form.email = 'adz@gmail.com'

        self.assertFalse( test_profile_form.is_valid() )

    def test_nothing(self):
        """
            User dont cheange anything
        """

        profile = self.u1.get_profile()

        test_profile_form = ProfileForm({'email':'borys.musielak@gmail.com'}, instance=profile)
        test_profile_form.email = 'borys.musielak@gmail.com'
        
        self.assertTrue( test_profile_form.is_valid() )
        

def suite():
    suite = unittest.TestSuite()
    suite.addTest(EmailValidationTestCase('test_new_mail'))
    suite.addTest(EmailValidationTestCase('test_same_mail'))
    suite.addTest(EmailValidationTestCase('test_nothing'))
   
    return suite
