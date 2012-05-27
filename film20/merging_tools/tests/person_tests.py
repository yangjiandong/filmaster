from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from film20.config.urls import urls
from film20.core.models import Person, Rating
from film20.merging_tools.models import DuplicatePerson
from film20.merging_tools.forms import ReportPersonDuplicateForm
from film20.core import rating_helper

class DuplicatePersonsTestCase( TestCase ):
    
    def setUp( self ):
        self.u1 = User.objects.create_user( "user", "user@user.com", "user" )
        self.u1.is_superuser = True
        self.u1.save()

        self.u2 = User.objects.create_user( "user2", "user2@user.com", "user2" )
        self.u3 = User.objects.create_user( "user3", "user3@user.com", "user3" )
        self.u4 = User.objects.create_user( "user4", "user4@user.com", "user4" )

        self.p1 = Person.objects.create( name='P1', surname='P1', permalink='p1', type=Person.TYPE_PERSON )
        self.p2 = Person.objects.create( name='P2', surname='P2', permalink='p2', type=Person.TYPE_PERSON )

        rating_helper.rate(self.u1, 5, director_id=self.p1.id, type=2)
        rating_helper.rate(self.u2, 2, director_id=self.p2.id, type=2)
        
        rating_helper.rate(self.u1, 1, actor_id=self.p1.id, type=3)
        rating_helper.rate(self.u2, 2, actor_id=self.p1.id, type=3)
        rating_helper.rate(self.u3, 3, actor_id=self.p1.id, type=3)
        
        rating_helper.rate(self.u1, 5, actor_id=self.p2.id, type=3)
        rating_helper.rate(self.u4, 6, actor_id=self.p2.id, type=3)

    def tearDown( self ):
        User.objects.all().delete()
        Person.objects.all().delete()

    def testFormValidation( self ):

        prefix = '%s/%s/' % ( settings.DOMAIN, urls['PERSON'] )

        form = ReportPersonDuplicateForm({ 
            'objectA': 'http://' + prefix + self.p1.permalink, 
            'objectB': 'http://' + prefix + self.p2.permalink 
        })
        self.assertTrue( form.is_valid() )

        form = ReportPersonDuplicateForm({ 
            'objectA': 'http://legia.com', 
            'objectB': 'http://google.pl' 
        })
        self.assertFalse( form.is_valid() )

    
    def testResolveDuplicate( self ):
        do, cr = DuplicatePerson.objects.get_or_create( user=self.u1, personA=self.p1, personB=self.p2 )
        
        data = {
            'A': 'true',
            'step': '3',
        }

        self.client.login( username='user', password='user' )
        response = self.client.post( reverse( 'people-merging-tool-resolve', args=[ do.pk ] ), data )
        self.assertEqual( response.status_code, 200 )

        self.p1 = Person.objects.get( pk=self.p1.pk )

        self.assertEqual( Rating.objects.filter( director=self.p1 ).count(), 2 )
        self.assertEqual( Rating.objects.filter( actor=self.p1 ).count(), 4 )
        self.assertEqual( Rating.objects.get( actor=self.p1, user=self.u1 ).rating, 1 )

