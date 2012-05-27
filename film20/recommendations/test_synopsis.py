#-*- coding: utf-8 -*-
import unittest
from film20.core.models import Film, ObjectLocalized, FilmLocalized, Object
from film20.recommendations.bot_helper import fetch_synopses_for_films_no_synopses,fetch_synopses_for_films_no_localized_film, fetch_synopses_for_films
from synopsis_helper import TmdbSynopsisFetcher

from django.conf import settings
LANGUAGE_CODE = getattr(settings, 'LANGUAGE_CODE', '')
from film20.utils.test import TestCase

class TmdbFetcherTestCase(TestCase):

    def test_fetcher(self):

        title = "The Terminator"
        url = "http://www.themoviedb.org/movie/218"
        year = 1984
        synopsis = "In the post-apocalyptic future, reigning tyrannical supercomputers teleport a cyborg assassin known as the \"Terminator\" back to 1984 to snuff Sarah Connor, whose unborn son is destined to lead insurgents against 21st century mechanical hegemony. Meanwhile, the human-resistance movement dispatches a lone warrior to safeguard Sarah. Can he stop the virtually indestructible killing machine?"

        fetcher = TmdbSynopsisFetcher()
        urls = fetcher.get_movie_urls(title, year)
        synopses = fetcher.get_movie_synopses(urls[0]['url'])

        self.assertEquals(synopses[0]['synopsis'], synopsis)
        self.assertEquals(synopses[0]['url'], url)
        self.assertEquals(synopses[0]['author'], "TMDb")
        self.assertEquals(synopses[0]['distributor'], False)
        self.assertEquals(synopses[0]['title'], title)

    def test_save_searchkeys(self):
        """
            Test saving searchkeys for localized film
        """
        self.film = Film()
        self.film.title = u"Olympia - Fest der Schönheit"
        self.film.type = Object.TYPE_FILM
        self.film.permalink = "olympia-2-teil-fest-der-schoenheit"
        self.film.release_year = 1938
        self.film.save()

        fetch_synopses_for_films([self.film,], fetcher="tmdb")

        loc_film = FilmLocalized.objects.all()[0]

        self.assertEquals(loc_film.description is None, True)
        self.assertEquals(loc_film.fetched_description is None, False)

class BotHelperTestCase(TestCase):

    def initialize(self):
        self.clean_data()
        self.create_films()


    def clean_data(self):
        Film.objects.all().delete()
        ObjectLocalized.objects.all().delete()
        FilmLocalized.objects.all().delete()


    def create_films(self):
        self.film1 = Film()
        self.film1.title = "The Terminator"
        self.film1.type = Object.TYPE_FILM
        self.film1.permalink = "the-terminator"
        self.film1.release_year = 1984
        self.film1.save()

        self.film2 = Film()
        self.film2.title = "Rambo"
        self.film2.type = Object.TYPE_FILM
        self.film2.permalink = "rambo"
        self.film2.release_year = 1982
        self.film2.save()


    def test_fetch_synopses_for_films_no_localized_film_nosynopsisindb(self):
        """
            There are two films in db both without synopsis
        """

        self.initialize()

        # there are no LocalizedFilms
        self.assertEquals(FilmLocalized.objects.all().count(), 0)

        fetch_synopses_for_films_no_localized_film(0,50)

        # there are two localized films
        loc_films = FilmLocalized.objects.all()
        self.assertEquals(loc_films.count(), 2)

        # both localized films should have fetched_description
        # and shouldn't have description
        loc_film1 = loc_films[0]
        self.assertEquals(loc_film1.description is None, True)
        self.assertEquals(loc_film1.fetched_description is None, False)

        loc_film2 = loc_films[1]
        self.assertEquals(loc_film2.description is None, True)
        self.assertEquals(loc_film2.fetched_description is None, False)


    def test_fetch_synopses_for_films_no_localized_film_onesynopsisindb(self):
        """
            There are two films in db but only one with localized object
        """
        self.initialize()

        # creating localized film and setting description by user
        loc_film = self.film1.get_or_create_film_localized(LANG=LANGUAGE_CODE)
        loc_film.description = "film description added by user"
        loc_film.save()

        # there is one LocalizedFilm
        self.assertEquals(FilmLocalized.objects.all().count(), 1)

        fetch_synopses_for_films_no_localized_film(0,50)

        # there are two localized films now
        loc_films = FilmLocalized.objects.all()
        self.assertEquals(loc_films.count(), 2)

        # First localized film was created by user and should be
        # touched by synopsis_fetcher
        loc_film1 = loc_films[0]
        self.assertEquals(loc_film1.description is None, False)
        self.assertEquals(loc_film1.description, "film description added by user")
        self.assertEquals(loc_film1.fetched_description is None, True)

        # Second localized film was created by fetcher
        loc_film2 = loc_films[1]
        self.assertEquals(loc_film2.description is None, True)
        self.assertEquals(loc_film2.fetched_description is None, False)


    def test_fetch_synopses_for_films_no_localized_film_twosynopsisindb(self):
        """
            There are two films in db both with localized objects
        """
        self.initialize()

        # Creating localized films first by user, second one by fetcher
        loc_film = self.film1.get_or_create_film_localized(LANG=LANGUAGE_CODE)
        loc_film.description = "film1 description added by user"
        loc_film.save()

        loc_film = self.film2.get_or_create_film_localized(LANG=LANGUAGE_CODE)
        loc_film.fetched_description = "film2 description added by fetcher"
        loc_film.fetched_description_url = "http://some.url"
        loc_film.fetched_description_url_text = "some url"
        loc_film.fetched_description_type = FilmLocalized.DESC_DISTRIBUTOR
        loc_film.save()

        # there are two LocalizedFilms
        self.assertEquals(FilmLocalized.objects.all().count(), 2)

        fetch_synopses_for_films_no_localized_film(0,50)

        # there are two localized films 
        loc_films = FilmLocalized.objects.all()
        self.assertEquals(loc_films.count(), 2)

        # Localized films were not changed by fetcher
        loc_film1 = loc_films[0]
        self.assertEquals(loc_film1.description is None, False)
        self.assertEquals(loc_film1.description, "film1 description added by user")
        self.assertEquals(loc_film1.fetched_description is None, True)

        loc_film2 = loc_films[1]
        self.assertEquals(loc_film2.description is None, True)
        self.assertEquals(loc_film2.fetched_description, "film2 description added by fetcher")
        self.assertEquals(loc_film2.fetched_description_url, "http://some.url")
        self.assertEquals(loc_film2.fetched_description_url_text, "some url")
        self.assertEquals(loc_film2.fetched_description_type, FilmLocalized.DESC_DISTRIBUTOR)


    def test_fetch_synopses_for_films_no_synopses_nolocalizedfilms(self):
        """
            There are two films in db both without localized films
        """

        self.initialize()

        # there are no LocalizedFilms
        self.assertEquals(FilmLocalized.objects.all().count(), 0)

        fetch_synopses_for_films_no_synopses(0,50)

        # there are two localized films - it OK, this
        # function in trying to fetch synopsis only for
        # films with localized films
        loc_films = FilmLocalized.objects.all()
        self.assertEquals(loc_films.count(), 0)


    def test_fetch_synopses_for_films_no_synopses_onelocalizedfilm(self):
        """
            There is one localized film, without description or fetched description
        """

        self.initialize()

        # there are no LocalizedFilms
        self.assertEquals(FilmLocalized.objects.all().count(), 0)

        loc_film = self.film1.get_or_create_film_localized(LANG=LANGUAGE_CODE)

        # There is only one localized film, without description or
        # fetched_description
        self.assertEquals(loc_film.description is None, True)
        self.assertEquals(loc_film.fetched_description is None, True)

        fetch_synopses_for_films_no_synopses(0,50)

        # There is still one localized film
        loc_films = FilmLocalized.objects.all()
        self.assertEquals(loc_films.count(), 1)

        loc_film1 = loc_films[0]

        # There should be fetched_description now for localized film
        self.assertEquals(loc_film1.description is None, True)
        self.assertEquals(loc_film1.fetched_description is None, False)


    def test_fetch_synopses_for_films_no_synopses_twolocalizedfilms(self):
        """
            There are two localized films, without description or fetched description
        """

        self.initialize()

        # there are no LocalizedFilms
        self.assertEquals(FilmLocalized.objects.all().count(), 0)

        loc_film1 = self.film1.get_or_create_film_localized(LANG=LANGUAGE_CODE)
        loc_film2 = self.film2.get_or_create_film_localized(LANG=LANGUAGE_CODE)

        # There are two localized films both without description or
        # fetched_description
        self.assertEquals(loc_film1.description is None, True)
        self.assertEquals(loc_film1.fetched_description is None, True)

        self.assertEquals(loc_film2.description is None, True)
        self.assertEquals(loc_film2.fetched_description is None, True)


        fetch_synopses_for_films_no_synopses(0,50)

        loc_films = FilmLocalized.objects.all()
        self.assertEquals(loc_films.count(), 2)

        loc_film1 = loc_films[0]

        # Both films has fetched_description
        self.assertEquals(loc_film1.description is None, True)
        self.assertEquals(loc_film1.fetched_description is None, False)

        loc_film2 = loc_films[1]

        self.assertEquals(loc_film2.description is None, True)
        self.assertEquals(loc_film2.fetched_description is None, False)


    def test_fetch_synopses_for_films_no_synopses_twolocalizedfilmswithsynopses(self):
        """
           There are two localized films, one with user synopsis, second with fetched synopsis
        """

        self.initialize()

        # there are no LocalizedFilms
        self.assertEquals(FilmLocalized.objects.all().count(), 0)

        # There are two localized films one with fetched description
        # second with description created by user
        loc_film = self.film1.get_or_create_film_localized(LANG=LANGUAGE_CODE)
        loc_film.description = "film1 description added by user"
        loc_film.save()

        loc_film2 = self.film2.get_or_create_film_localized(LANG=LANGUAGE_CODE)
        loc_film2.fetched_description = "film2 description added by fetcher"
        loc_film2.fetched_description_url = "http://some.url"
        loc_film2.fetched_description_url_text = "some url"
        loc_film2.fetched_description_type = FilmLocalized.DESC_DISTRIBUTOR
        loc_film2.save()

        fetch_synopses_for_films_no_synopses(0,50)

        # there are two localized films
        loc_films = FilmLocalized.objects.all()
        self.assertEquals(loc_films.count(), 2)

        # Localized films were not changed by fetcher
        loc_film1 = loc_films[0]
        self.assertEquals(loc_film1.description is None, False)
        self.assertEquals(loc_film1.description, "film1 description added by user")
        self.assertEquals(loc_film1.fetched_description is None, True)

        loc_film2 = loc_films[1]
        self.assertEquals(loc_film2.description is None, True)
        self.assertEquals(loc_film2.fetched_description, "film2 description added by fetcher")
        self.assertEquals(loc_film2.fetched_description_url, "http://some.url")
        self.assertEquals(loc_film2.fetched_description_url_text, "some url")
        self.assertEquals(loc_film2.fetched_description_type, FilmLocalized.DESC_DISTRIBUTOR)

        
from film20.recommendations.synopsis_helper import WikipediaFetcher
from film20.utils.test import integration_test
class WikipediaFetcherTestCase(TestCase):
    @integration_test
    def test_fetcher(self):

        titles = [
            { 
              'title'   : 'Leon',
              'year'    : 1994,
              'url'     : "http://en.wikipedia.org/wiki/Leon_(film)", 
              'synopsis': u"Leone \"Léon\" Montana (Jean Reno) is a hitman (or \"cleaner,\" as he refers to himself) living a solitary life in New York City's Little Italy. His work comes from a mafioso named Tony (Danny Aiello), who operates from the \"Supreme Macaroni Company\" restaurant. Léon spends his idle time engaging in calisthenics, nurturing a houseplant that early on he describes as his \"best friend,\" and (in one scene) watching old Gene Kelly musicals."
            },{ 
              'title'   : 'Avatar',
              'year'    : 2009,
              'url'     : "http://en.wikipedia.org/wiki/Avatar_(2009_film)", 
              'synopsis': u"By 2148, humans have severely depleted Earth's natural resources. In 2154, the RDA Corporation mines for a valuable mineral—unobtanium—on Pandora, a densely-forested habitable moon of the gas giant Polyphemus in the Alpha Centauri star system. Pandora, whose atmosphere is poisonous to humans, is inhabited by the Na'vi, 10-foot (3.0 m)-tall, blue-skinned, sapient humanoids who live in harmony with nature and worship a mother goddess called Eywa."
            },
        ]


        for item in titles:
            fetcher = WikipediaFetcher()
            urls = fetcher.get_movie_urls( item['title'], item['year'] )
            self.assertTrue( len( urls ) > 0 )

            synopses = fetcher.get_movie_synopses( urls[0]['url'] )
            self.assertEquals( synopses[0]['synopsis'], item['synopsis'] )
            self.assertEquals( synopses[0]['url'], item['url'] )
            self.assertEquals( synopses[0]['author'], "Wikipedia" )
            self.assertEquals( synopses[0]['distributor'], False )

