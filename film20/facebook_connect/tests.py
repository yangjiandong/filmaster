from django.utils import unittest
from film20.utils.test import integration_test, TestCase

from .url_matcher import FacebookMatcher, FilmwebMatcher, WikipediaMatcher, IMDBMatcher, FilmasterMatcher
from .models import FBMovie

class URLMatcherTest(TestCase):
    fixtures = ['test_films.json']
    @integration_test
    def test_facebook(self):
        data = FacebookMatcher('http://www.facebook.com/PulpFiction')
        self.assertEquals(data.title, 'Pulp Fiction')
        self.assertEquals(data.directors, ['Quentin Tarantino'])

        data = FacebookMatcher('http://www.facebook.com/pages/Ghost-in-the-Shell/111961145486420')
        self.assertEquals(data.title, 'Ghost in the Shell')
        self.assertEquals(data.directors, ['Mamoru Oshii'])

    @integration_test
    def test_filmweb(self):
        data = FilmwebMatcher('http://www.filmweb.pl/Pulp.Fiction')
        self.assertEquals(data.title, 'Pulp Fiction')
        self.assertEquals(data.directors, ['Quentin Tarantino'])

    @integration_test
    def test_wikipedia(self):
        data = WikipediaMatcher('http://en.wikipedia.org/wiki/Pulp_Fiction')
        self.assertEquals(data.title, 'Pulp Fiction')
        self.assertEquals(data.directors, ['Quentin Tarantino'])

    def test_url_parsers(self):
        data = IMDBMatcher('http://www.imdb.com/title/tt0110912/')
        self.assertEquals(data.imdb_code, '0110912')

        data = FilmasterMatcher('http://filmaster.pl/film/pulp-fiction/')
        self.assertEquals(data.permalink, 'pulp-fiction')

    def test_matching(self):
        from film20.core.models import Film, Person
        from film20.showtimes.models import FilmOnChannel
        
        film = Film.objects.get(permalink='pulp-fiction')
        d = Person.objects.create(name='Quentin', surname='Tarantino', type=Person.TYPE_PERSON)
        film.directors.add(d)
        movie = FBMovie.objects.create(link='http://www.imdb.com/title/tt0110912/', id=1)
        self.assertTrue(Film.objects.match('Pulp Fiction', directors=['Quentin Tarantino']))
        self.assertTrue(movie.film)

        movie = FBMovie.objects.create(link='http://www.imdb.com/title/tt1675434/', id=2)
        self.assertFalse(movie.film)
        foc = FilmOnChannel.objects.get(key='http://www.imdb.com/title/tt1675434/')

        # manual match
        foc.film = film
        foc.save()
        movie = FBMovie.objects.get(id=2)
        self.assertTrue(movie.film)

