from django.test import TestCase
from django.contrib.auth.models import User

from film20.core.models import Film, SimilarFilm

class SimilarFilmsTestCase( TestCase ):

    def setUp( self ):
        self.u1 = User.objects.create_user( "user1", "user1@user.com", "user" )
        self.u2 = User.objects.create_user( "user2", "user2@user.com", "user" )
        self.u3 = User.objects.create_user( "user3", "user3@user.com", "user" )

        self.f1 = Film()
        self.f1.title = "Battlefield Earth"
        self.f1.type = Film.TYPE_FILM
        self.f1.permalink = "battlefirld-earth"
        self.f1.release_year = 208
        self.f1.production_country_list = "USA"
        self.f1.save()

        self.f2 = Film()
        self.f2.title = "Battlefield Earth II"
        self.f2.type = Film.TYPE_FILM
        self.f2.permalink = "battlefirld-earth-ii"
        self.f2.release_year = 2010
        self.f2.production_country_list = "USA"
        self.f2.save()

    def tearsDown( self ):
        Film.objects.all().delete()
        SimilarFilm.objects.all().delete()

    def test_votes( self ):
        SimilarFilm.add_vote( user=self.u1, film_a=self.f1, film_b=self.f2 )#1
        SimilarFilm.add_vote( user=self.u2, film_a=self.f1, film_b=self.f2 )#2
        SimilarFilm.add_vote( user=self.u3, film_a=self.f1, film_b=self.f2 )#3
        
        SimilarFilm.add_vote( user=self.u3, film_a=self.f2, film_b=self.f1 )#4
        

        self.assertEqual( SimilarFilm.objects.filter( film_a=self.f1 ).count(), 1 )
        
        similar = SimilarFilm.objects.get( film_a=self.f1 )
        self.assertEqual( similar.number_of_votes, 3 )

        SimilarFilm.remove_vote( user=self.u1, film_a=self.f1, film_b=self.f2 )#2

        similar = SimilarFilm.objects.get( film_a=self.f1 )
        self.assertEqual( similar.number_of_votes, 2 )

        SimilarFilm.remove_vote( user=self.u2, film_a=self.f1, film_b=self.f2 )#1

        similar = SimilarFilm.objects.get( film_a=self.f1 )
        self.assertEqual( similar.number_of_votes, 1 )

        SimilarFilm.remove_vote( user=self.u3, film_a=self.f1, film_b=self.f2 )#1

        self.assertEqual( SimilarFilm.objects.filter( film_a=self.f1 ).count(), 0 )
