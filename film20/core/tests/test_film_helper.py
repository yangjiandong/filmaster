from decimal import Decimal
from film20.utils.test import TestCase
from film20.core.models import Film, Object, FilmComparator, FilmRanking, \
        Rating, User
from film20.core.film_helper import FilmHelper

class FilmHelperTestCase(TestCase):

    def initialize(self):
        self.clean_data()

        tags = "sciencie-fiction comedy"

        # set up test user
        self.user1 = User.objects.create_user("user1", "user@user.com", "secret")
        self.user1.save()


        # set up films
        self.film1 = Film()
        self.film1.title = "Battlefield Earth II"
        self.film1.type = Object.TYPE_FILM
        self.film1.permalink = "battlefirld-earth-ii"
        self.film1.release_year = 2010
        self.film1.production_country_list = "USA"
        self.film1.save()
        self.film1.save_tags(tags, LANG="pl", saved_by=2)

        self.film2 = Film()
        self.film2.title = "Battlefield Earth III"
        self.film2.type = Object.TYPE_FILM
        self.film2.permalink = "battlefirld-earth-iii"
        self.film2.release_year = 2011
        self.film2.production_country_list = "USA"
        self.film2.save()
        self.film2.save_tags(tags, LANG="pl", saved_by=2)

        self.film3 = Film()
        self.film3.title = "Battlefield Earth IV"
        self.film3.type = Object.TYPE_FILM
        self.film3.permalink = "battlefirld-earth-iv"
        self.film3.release_year = 2012
        self.film3.production_country_list = "Italy"
        self.film3.save()
        self.film3.save_tags(tags, LANG="pl", saved_by=2)

        self.film4 = Film()
        self.film4.title = "Battlefield Earth V"
        self.film4.type = Object.TYPE_FILM
        self.film4.permalink = "battlefirld-earth-v"
        self.film4.release_year = 2013
        self.film4.production_country_list = "UK"
        self.film4.save()
        self.film4.save_tags(tags, LANG="pl", saved_by=2)

        # set up filmrankings
        self.filmranking1 = FilmRanking()
        self.filmranking1.film = self.film1
        self.filmranking1.type = Rating.TYPE_FILM
        self.filmranking1.average_score = Decimal('8.0')
        self.filmranking1.number_of_votes = 80
        self.filmranking1.save()
        
        self.filmranking2 = FilmRanking()
        self.filmranking2.film = self.film2
        self.filmranking2.type = Rating.TYPE_FILM
        self.filmranking2.average_score = Decimal('7.0')
        self.filmranking2.number_of_votes = 70
        self.filmranking2.save()

        self.filmranking3 = FilmRanking()
        self.filmranking3.film = self.film3
        self.filmranking3.type = Rating.TYPE_FILM
        self.filmranking3.average_score = Decimal('6.0')
        self.filmranking3.number_of_votes = 60
        self.filmranking3.save()

        self.filmranking4 = FilmRanking()
        self.filmranking4.film = self.film4
        self.filmranking4.type = Rating.TYPE_FILM
        self.filmranking4.average_score = Decimal('5.0')
        self.filmranking4.number_of_votes = 2
        self.filmranking4.save()

        # save compared objects in database
        self.compared_film1 = FilmComparator()
        self.compared_film1.main_film = self.film1
        self.compared_film1.compared_film = self.film1
        self.compared_film1.score = 10
        self.compared_film1.save()

        self.compared_film2 = FilmComparator()
        self.compared_film2.main_film = self.film1
        self.compared_film2.compared_film = self.film2
        self.compared_film2.score = 9
        self.compared_film2.save()

        self.compared_film3 = FilmComparator()
        self.compared_film3.main_film = self.film1
        self.compared_film3.compared_film = self.film3
        self.compared_film3.score = 8
        self.compared_film3.save()

        self.compared_film4 = FilmComparator()
        self.compared_film4.main_film = self.film1
        self.compared_film4.compared_film = self.film4
        self.compared_film4.score = 7
        self.compared_film4.save()

        # set up test user ratings
        self.user1rating1 = Rating()
        self.user1rating1.type = Rating.TYPE_FILM
        self.user1rating1.user = self.user1
        self.user1rating1.film = self.film1
        self.user1rating1.parent = self.film1
        self.user1rating1.rating = 10
        self.user1rating1.save()

        self.user1rating2 = Rating()
        self.user1rating2.type = Rating.TYPE_FILM
        self.user1rating2.user = self.user1
        self.user1rating2.film = self.film2
        self.user1rating2.parent = self.film2
        self.user1rating2.rating = 9
        self.user1rating2.save()

        self.user1rating3 = Rating()
        self.user1rating3.type = Rating.TYPE_FILM
        self.user1rating3.user = self.user1
        self.user1rating3.film = self.film3
        self.user1rating3.parent = self.film3
        self.user1rating3.rating = 8
        self.user1rating3.save()

        self.user1rating4 = Rating()
        self.user1rating4.type = Rating.TYPE_FILM
        self.user1rating4.user = self.user1
        self.user1rating4.film = self.film4
        self.user1rating4.parent = self.film4
        self.user1rating4.rating = 7
        self.user1rating4.save()

    def clean_data(self):
        Film.objects.all().delete()
        FilmComparator.objects.all().delete()
        FilmRanking.objects.all().delete()

    def test_get_users_best_films(self):
        """
            Test get_users_best_films method
        """

        self.initialize()
        helper = FilmHelper()
        best_films = helper.get_users_best_films(self.user1, 3)
        self.assertEquals(len(best_films), 3)
        self.assertEquals(self.film4 in best_films, False)
        self.assertEquals(self.film1 in best_films, True)

    def test_get_related_localized_objects(self):
        """
            Test get_related_localized_objects() method 
        """

        self.initialize()
        helper = FilmHelper()
        related = helper.get_related_localized_objects(self.film1, 3)
        self.assertEquals(len(related), 3)

    def test_get_popular_films(self):
        """
            Test get_popular_films method
        """

        self.initialize()
        helper = FilmHelper()

        films_english = set(helper.get_popular_films(exclude_nonEnglish=True))
        self.assertEquals(self.film1 in films_english, True)
        self.assertEquals(self.film3 in films_english, False)
        self.assertEquals(self.film4 in films_english, False)

        films_english = set(helper.get_popular_films())
        self.assertEquals(self.film1 in films_english, True)
        self.assertEquals(self.film3 in films_english, True)


