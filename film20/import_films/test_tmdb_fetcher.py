from film20.utils.test import TestCase, integration_test
from film20.core.models import Film, Object
from film20.import_films.tmdb_poster_fetcher import fetch_film_by_title, save_tmdb_poster, fetch_film_by_id

class TmdbPosterFetcherTestCase(TestCase):

    film = None


    def clean_data(self):
        Film.objects.all().delete()
        Object.objects.all().delete()

    def initialize(self):

        self.clean_data()

        film = Film()
        film.title = "The Terminator"
        film.type = Object.TYPE_FILM
        film.imdb_code = "0088247"
        film.permalink = "the-terminator"
        film.release_year = 1984
        film.save()
        self.film = film

    @integration_test
    def test_fetch_by_title(self):
        """
           Test fetching by title
        """
        self.initialize()

        films = Film.objects.filter(image="", tmdb_import_status=Film.NOT_IMPORTED)
        for film in films:
            tmdb_movie = fetch_film_by_title(film)
            self.assertEqual(tmdb_movie is not None, True)
            result = save_tmdb_poster(film, tmdb_movie)
            self.assertEqual(result, True)

        film = Film.objects.get(title="The Terminator")
        self.assertEqual(film.image is not None, True)

    @integration_test
    def test_fetch_by_id(self):
        """
           Test fetching by imdb code
        """
        self.initialize()

        films = Film.objects.filter(image="", tmdb_import_status=Film.NOT_IMPORTED)
        for film in films:
            self.assertEqual(film.image is not None, True)
            tmdb_movie = fetch_film_by_id(film)
            self.assertEqual(tmdb_movie is not None, True)
            result = save_tmdb_poster(film, tmdb_movie)
            self.assertEqual(result, True)

        film = Film.objects.get(title="The Terminator")
        self.assertEqual(film.image is not None, True)

    def test_tmdb_status(self):
        """
           Test tmdb_status
        """
        self.initialize()
        # take all not imported movies without posters from db
        films = Film.objects.filter(image="", tmdb_import_status=Film.NOT_IMPORTED)
        # there should be only 1 movie
        self.assertEqual(len(films), 1)
        #try to fetch posters
        for film in films:
            # check if there is no poster
            self.assertEqual(film.image is not None, True)
            # check tmdb_import_status, should be NOT_IMPORTED
            self.assertEqual(film.tmdb_import_status, Film.NOT_IMPORTED)
            # fetch poster for film
            tmdb_movie = fetch_film_by_id(film)
            film.tmdb_import_status = Film.IMPORTED
            film.save()
            self.assertEqual(tmdb_movie is not None, True)
            result = save_tmdb_poster(film, tmdb_movie)
            self.assertEqual(result, True)

        film = Film.objects.get(title="The Terminator")
        # check tmdb_status should be IMPORTED
        self.assertEqual(film.tmdb_import_status, Film.IMPORTED)

        # there are no other movies without posters in db
        films = Film.objects.filter(tmdb_import_status=Film.NOT_IMPORTED)
        self.assertEqual(len(films), 0)
