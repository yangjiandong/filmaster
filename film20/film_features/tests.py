import random

from django.test import TestCase
from django.contrib.auth.models import User

from film20.core import rating_helper
from film20.core.models import Film, Rating, SimilarFilm
from film20.film_features.models import FilmFeature, FilmFeatureVote, FilmFeatureComparisionVote

class FilmFeaturesTest( TestCase ):

    def setUp( self ):
        self.u1 = User.objects.create_user( "user1", "user1@user.com", "user" )
        self.u2 = User.objects.create_user( "user2", "user2@user.com", "user" )
        self.u3 = User.objects.create_user( "user3", "user3@user.com", "user" )

        self.films = []
        for i in range(10):
            f = Film.objects.create(
                permalink="test-film-%d" % i,
                title="title %2d" % i,
                type=Film.TYPE_FILM,
                release_year=2000,
            )
            rating_helper.rate( self.u1, random.randint( 1, 5 ), film_id=f.pk )
            rating_helper.rate( self.u2, random.randint( 1, 5 ), film_id=f.pk )

            self.films.append( f )

        SimilarFilm.add_vote( self.u2, self.films[1], self.films[2] )
        SimilarFilm.add_vote( self.u3, self.films[2], self.films[1] )

        SimilarFilm.add_vote( self.u2, self.films[2], self.films[4] )

        rating_helper.rate( self.u3, 3, film_id=self.films[2].pk )

    def tearsDown( self ):
        Film.objects.all().delete()
        Rating.objects.all().delete()
        FilmFeature.objects.all().delete()
        FilmFeatureVote.objects.all().delete()
        FilmFeatureComparisionVote.objects.all().delete()

    def test_votes( self ):
        v1 = FilmFeatureVote.objects.create( user=self.u1, film=self.films[1], type=1 )
        v2 = FilmFeatureVote.objects.create( user=self.u2, film=self.films[1], type=1 )
        v3 = FilmFeatureVote.objects.create( user=self.u3, film=self.films[1], type=1 )
        
        v4 = FilmFeatureVote.objects.create( user=self.u1, film=self.films[1], type=2 )

        self.assertEqual( FilmFeature.objects.filter( film=self.films[1] ).count(), 2 )
        self.assertEqual( FilmFeature.objects.filter( film=self.films[1], type=1 ).count(), 1 )
        
        ff = FilmFeature.objects.get( film=self.films[1], type=1 )
        self.assertEqual( ff.number_of_votes, 3 )

        v1.delete()

        ff = FilmFeature.objects.get( film=self.films[1], type=1 )
        self.assertEqual( ff.number_of_votes, 2 )

        v2.delete()

        ff = FilmFeature.objects.get( film=self.films[1], type=1 )
        self.assertEqual( ff.number_of_votes, 1 )

        v3.delete()

        self.assertEqual( FilmFeature.objects.filter( film=self.films[1], type=1 ).count(), 0 )
        self.assertEqual( FilmFeature.objects.filter( film=self.films[1] ).count(), 1 )

    def test_comparision( self ):
        FilmFeatureComparisionVote.objects.store_result( self.u1, self.films[1], self.films[2], 1 )
        FilmFeatureComparisionVote.objects.store_result( self.u2, self.films[1], self.films[2], 1, result=self.films[1] )
        FilmFeatureComparisionVote.objects.store_result( self.u3, self.films[1], self.films[2], 1, result=self.films[2] )
        
        self.assertEqual( FilmFeatureComparisionVote.objects.count(), 3 )
        
        FilmFeatureComparisionVote.objects.store_result( self.u3, self.films[1], self.films[2], 1, result=self.films[1] )
        
        self.assertEqual( FilmFeatureComparisionVote.objects.count(), 3 )
        

        self.assertTrue( FilmFeatureComparisionVote.objects.is_voted( self.u1, self.films[1], self.films[2], 1 ) )
        self.assertTrue( FilmFeatureComparisionVote.objects.is_voted( self.u1, self.films[2], self.films[1], 1 ) )

        self.assertFalse( FilmFeatureComparisionVote.objects.is_voted( self.u1, self.films[1], self.films[2], 2 ) )
        self.assertFalse( FilmFeatureComparisionVote.objects.is_voted( self.u1, self.films[2], self.films[1], 2 ) )

    def test_next_to_compare( self ):
        self.assertEqual( Rating.objects.count(), 21 )

        FilmFeatureVote.objects.create( user=self.u1, film=self.films[1], type=1 )
        FilmFeatureVote.objects.create( user=self.u2, film=self.films[1], type=1 )
        FilmFeatureVote.objects.create( user=self.u3, film=self.films[2], type=1 )

        FilmFeatureVote.objects.create( user=self.u2, film=self.films[2], type=2 )
        FilmFeatureVote.objects.create( user=self.u3, film=self.films[4], type=2 )

        FilmFeatureVote.objects.create( user=self.u3, film=self.films[5], type=5 )
        FilmFeatureVote.objects.create( user=self.u3, film=self.films[6], type=5 )
        
        cv1 = FilmFeatureComparisionVote.objects.next_to_vote( self.u1 )
        self.assertTrue( cv1 is not None )

        cv2 = FilmFeatureComparisionVote.objects.next_to_vote( self.u1 )
        self.assertEqual( cv1.pk, cv2.pk )
        
        FilmFeatureComparisionVote.objects.store_result( self.u1, cv2.film_a, cv2.film_b, cv2.feature )# skip

        cv3 = FilmFeatureComparisionVote.objects.next_to_vote( self.u1 )
        self.assertTrue( cv3 is not None )
        self.assertNotEquals( cv2.pk, cv3.pk )
        
        FilmFeatureComparisionVote.objects.store_result( self.u1, cv3.film_a, cv3.film_b, cv3.feature, cv3.film_a )# a is more brutal

        cv4 = FilmFeatureComparisionVote.objects.next_to_vote( self.u1 )
        self.assertTrue( cv4 is not None )

        cv5 = FilmFeatureComparisionVote.objects.next_to_vote( self.u1 )
        self.assertTrue( cv5 is not None )
        self.assertEqual( cv4.pk, cv5.pk )

        cv6 = FilmFeatureComparisionVote.objects.next_to_vote( self.u1 )
        self.assertTrue( cv6 is not None )
        self.assertEqual( cv5.pk, cv6.pk )

        FilmFeatureComparisionVote.objects.store_result( self.u1, cv6.film_a, cv6.film_b, cv6.feature, cv6.film_b )# b is more warm

        cv7 = FilmFeatureComparisionVote.objects.next_to_vote( self.u1 )
        self.assertTrue( cv7 is None )
