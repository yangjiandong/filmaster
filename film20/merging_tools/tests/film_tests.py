from django.conf import settings
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from film20.config.urls import urls
from film20.core.models import Film, Object, Rating
from film20.core import rating_helper
from film20.merging_tools.models import DuplicateFilm
from film20.merging_tools.forms import ReportFilmDuplicateForm

class DuplicateFilmsTestCase( TestCase ):
    
    def setUp( self ):
        self.u1 = User.objects.create_user( "user", "user@user.com", "user" )
        self.u1.is_superuser = True
        self.u1.save()

        self.u2 = User.objects.create_user( "user2", "user2@user.com", "user2" )
        self.u3 = User.objects.create_user( "user3", "user3@user.com", "user3" )
        self.u4 = User.objects.create_user( "user4", "user4@user.com", "user4" )

        self.f1 = Film()
        self.f1.title = "Battlefield Earth II"
        self.f1.type = Object.TYPE_FILM
        self.f1.permalink = "battlefirld-earth-ii"
        self.f1.release_year = 2010
        self.f1.production_country_list = "USA"
        self.f1.save()
        self.f1.save_tags( "sciencie-fiction komedia test1 test2", LANG="pl", saved_by=2)

        self.f2 = Film()
        self.f2.title = "Battlefield Earth II 2"
        self.f2.type = Object.TYPE_FILM
        self.f2.permalink = "battlefirld-earth-ii-2"
        self.f2.release_year = 2010
        self.f2.production_country_list = "USA"
        self.f2.save()
        self.f2.save_tags( "sciencie komedia test1", LANG="pl", saved_by=2)

        rating_helper.rate(self.u1, 1, self.f1.id)
        rating_helper.rate(self.u1, 2, self.f2.id)
        rating_helper.rate(self.u2, 3, self.f1.id)
        rating_helper.rate(self.u3, 3, self.f1.id)
        rating_helper.rate(self.u4, 3, self.f2.id)

    def tearDown( self ):
        User.objects.all().delete()
        Film.objects.all().delete()

    def testFormValidation( self ):

        prefix = '%s/%s/' % ( settings.DOMAIN, urls['FILM'] )

        form = ReportFilmDuplicateForm({ 
            'objectA': 'http://' + prefix + self.f1.permalink, 
            'objectB': 'http://' + prefix + self.f2.permalink 
        })
        self.assertTrue( form.is_valid() )

        form = ReportFilmDuplicateForm({ 
            'objectA': 'http://legia.com', 
            'objectB': 'http://google.pl' 
        })
        self.assertFalse( form.is_valid() )

    
    def testResolveDuplicate( self ):
        do, cr = DuplicateFilm.objects.get_or_create( user=self.u1, filmA=self.f1, filmB=self.f2 )
        
        data = {
            'A': 'true',
            'step': '3',
        }

        self.client.login( username='user', password='user' )
        response = self.client.post( reverse( 'movie-merging-tool-resolve', args=[ do.pk ] ), data )
        self.assertEqual( response.status_code, 200 )

        self.f1 = Film.objects.get( pk=self.f1.pk )

        self.assertEqual( len(rating_helper.get_film_ratings(self.f1.id)), 4 )
        self.assertEqual( rating_helper.get_rating(self.u1, self.f1.id), 1)
