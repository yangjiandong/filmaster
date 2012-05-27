import unittest, urllib2, time
from django.contrib.auth.models import User
from django.conf import settings
from film20.utils.test import TestCase 
from django.test.client import Client

def to_sub( user ):
    return '%s.%s' % (user.username, settings.DOMAIN)

# TODO find way to test own subdomain

class UserSubdomainTestCase( TestCase ):
    def setUp( self ):
        User.objects.all().delete()

        self.u1 = User(username='dupa', email='fake@fake.com')
        self.u2 = User(username='root', email='root@toor.com')
        self.u2.save()

    def testDoesUserExists( self ):
        r1 = self.client.get('/', HTTP_HOST=to_sub(self.u1))
        self.assertEquals( r1.status_code, 404 )
        
        r2 = self.client.get('/', HTTP_HOST=to_sub(self.u2))
        self.assertEquals( r2.status_code, 200 )
