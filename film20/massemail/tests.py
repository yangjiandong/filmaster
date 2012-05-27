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

from django.core import mail
from film20.utils.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from film20.core.models import Profile
from film20.massemail.helper import sendMassEmail
from film20.massemail.models import MassEmail


def createUserWithProfile( login, email, passwd, lang ):
    user = User.objects.create_user( login, email, passwd )
    profile, created = Profile.objects.get_or_create( user=user )
    profile.LANG = lang
    profile.save()
    
    return user, profile

def createUserWithProfileMobile( login, email, passwd, lang, platform ):
    user, profile = createUserWithProfile( login, email, passwd, lang )
    profile.mobile_platform = platform
    profile.save()
    
    return user, profile

class MassEmailTest( TestCase ):

    def setUp( self ):
        self.u, p = createUserWithProfile(  "user", "user@user.com", "user", "en" )
        
        self.u1, p1 = createUserWithProfile( "user1", "user1@user.com", "user1", "en" )
        self.u2, p2 = createUserWithProfile( "user2", "user2@user.com", "user2", "en" )
        self.u3, p3 = createUserWithProfile( "user3", "user3@user.com", "user3", "pl" )

        self.u4, p4 = createUserWithProfileMobile( "user4", "user4@user.com", "user4", "pl", "iphone" )
        self.u5, p5 = createUserWithProfileMobile( "user5", "user5@user.com", "user5", "pl", "iphone" )
        self.u6, p6 = createUserWithProfileMobile( "user6", "user6@user.com", "user6", "pl", "blackberry" )

    def tearDown( self ):
        mail.outbox = []

        User.objects.all().delete()
        Profile.objects.all().delete()
        MassEmail.objects.all().delete()

    def assertSentCorrectly(self, s1, s2):
        return self.assertEquals(set(s1.split(';')), set(s2.split(';')))

    def test_send_massemail( self ):
        massemail = MassEmail( subject='Test Email', body='<p>Some content...</p>', created_by=self.u, lang='en' )
        massemail.save()

        sendMassEmail( massemail )

        self.assertEqual( Profile.objects.count(), 7 )

        massemail = MassEmail.objects.get( pk=massemail.pk )

        self.assertEqual( len( mail.outbox ), 2 )
        self.assertEqual( massemail.body, mail.outbox[0].body )
        self.assertEqual( massemail.subject, mail.outbox[0].subject )

        self.assertEqual( massemail.sent_failed, 0 )
        self.assertEqual( massemail.sent_correctly, 2 )

        self.assertEqual( massemail.sent_failed_to, None )
        self.assertSentCorrectly( massemail.sent_correctly_to, 'user1@user.com;user2@user.com' )

        mail.outbox = []
        
        massemail.is_processed = False
        massemail.sent_correctly_to = 'user1@user.com'
        massemail.save()
        
        sendMassEmail( massemail )
        
        self.assertEqual( len( mail.outbox ), 1 )
        self.assertTrue( 'user2@user.com' in mail.outbox[0].recipients() )

        massemail = MassEmail.objects.get( pk=massemail.pk )
        
        self.assertEqual( massemail.sent_failed, 0 )
        self.assertEqual( massemail.sent_correctly, 2 )

        self.assertEqual( massemail.sent_failed_to, None )
        self.assertSentCorrectly( massemail.sent_correctly_to, 'user1@user.com;user2@user.com' )

    def test_send_massemail_mobile( self ):
        massemail = MassEmail( subject='Test Email', body='<p>Some content...</p>', created_by=self.u, lang='pl', mobile_platform='iphone' )
        massemail.save()

        sendMassEmail( massemail )

        massemail = MassEmail.objects.get( pk=massemail.pk )

        self.assertEqual( len( mail.outbox ), 2 )
        
        self.assertEqual( massemail.sent_failed, 0 )
        self.assertEqual( massemail.sent_correctly, 2 )

        self.assertEqual( massemail.sent_failed_to, None )
        self.assertSentCorrectly( massemail.sent_correctly_to, 'user4@user.com;user5@user.com' )

    def testSendMassEmailsCommand( self ):
 
        massemail1 = MassEmail( subject='Test Email1', body='<p>Some content1...</p>', created_by=self.u, lang='pl', mobile_platform='iphone' )
        massemail1.save()

        massemail2 = MassEmail( subject='Test Email2', body='<p>Some content2...</p>', created_by=self.u, lang='pl', mobile_platform='iphone' )
        massemail2.save()

        self.assertEqual( MassEmail.objects.filter( is_processed=False ).count(), 2 )

        call_command( 'send_massemails' )
        
        self.assertEqual( MassEmail.objects.filter( is_processed=False ).count(), 0 )

        self.assertEqual( len( mail.outbox ), 4 )
