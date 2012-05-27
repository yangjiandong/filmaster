# -*- coding: utf-8 -*-
from django.utils import unittest
from django.conf import settings

from film20.utils.test import TestCase, integration_test
from film20.import_films.models import FilmToImport, ImportedFilm
from django.contrib.auth.models import User
from film20.import_films.imdb_fetcher import run
from film20.core.models import Object, Film, Person

class ImdbFetcherTestCase(TestCase):

    user = None

    def clean_data(self):
        User.objects.all().delete()
        Object.objects.all().delete()
        FilmToImport.objects.all().delete()
        ImportedFilm.objects.all().delete()

    def initialize(self):
        self.clean_data()

        self.user= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.user.save()

    @integration_test
    def test_successfullfetch(self):
        """
           Test successfull fetch
        """

        self.client.login(username=self.user.username, password='secret')
        
        self.initialize()

        film_to_import = FilmToImport(user = self.user,
                                  title = 'Elektroniczny Morderca',
                                  imdb_url = 'http://www.imdb.com/title/tt0088247/',
					              imdb_id='0088247',
                                  status=FilmToImport.ACCEPTED)

        film_to_import.save()

        run(False, False, False, False, False, True, "http")

        # there is only 1 film to import in db
        film_to_import = FilmToImport.objects.get(id=1)

        self.assertEqual(film_to_import.is_imported, True)

        #film is imported
        imported_film = ImportedFilm.objects.get(id=1)

        self.assertEqual(imported_film.film.permalink, "the-terminator")

        film = Film.objects.get(permalink="the-terminator")
        self.assertEqual(film.permalink, "the-terminator")
        self.assertEqual(film.imdb_code, "0088247")
        self.assertEqual(film.title, "The Terminator")
        self.assertEqual(film.release_year, 1984)
        self.assertEqual(film.image is not None, True)
        self.assertEqual(film.production_country_list, "UK,USA")

    @integration_test
    def test_filmindb(self):
        """
            Test failed fetch movie in db
        """
        self.initialize()

        self.client.login(username=self.user.username, password='secret')

        film_to_import = FilmToImport(user = self.user,
                                  title = 'Elektroniczny Morderca',
                                  imdb_url = 'http://www.imdb.com/title/tt0088247/',
					              imdb_id='0088247',
                                  status=FilmToImport.ACCEPTED)

        film_to_import.save()

        film = Film()
        film.title = "The Terminator"
        film.type = Object.TYPE_FILM
        film.imdb_code = "0088247"
        film.permalink = "the-terminator"
        film.release_year = 1984
        film.save()

        run(False, False, False, False, False, True, "http")

        film_to_import = FilmToImport.objects.get(title = 'Elektroniczny Morderca')
        self.assertEqual(film_to_import.attempts, 1)
        self.assertEqual(film_to_import.status, FilmToImport.ALREADY_IN_DB)

    @integration_test
    def test_tvseries(self):
        """
           Film to import is a tv series or something went wrong
           during fetching page from imdb
        """
        self.initialize()

        self.client.login(username=self.user.username, password='secret')

        film_to_import = FilmToImport(user = self.user,
                                  title = 'The A-Team',
                                  imdb_url = 'http://www.imdb.com/title/tt0084967/',
					              imdb_id='0084967',
                                  status=FilmToImport.ACCEPTED)

        film_to_import.save()

        run(False, False, False, False, False, True, "http")

        film_to_import = FilmToImport.objects.get(title = 'The A-Team')
        self.assertEqual(film_to_import.status, FilmToImport.TV_SERIES)

    @integration_test
    def test_posterfetch(self):
        """
           Test case when there is no poster in imdb and poster is in tmdb db
        """

        self.initialize()

        self.client.login(username=self.user.username, password='secret')

        film_to_import = FilmToImport(user = self.user,
                                  title = 'Zaat',
                                  imdb_url = 'http://www.imdb.com/title/tt0072666/',
					              imdb_id='0072666',
                                  status=FilmToImport.ACCEPTED)

        film_to_import.save()

        run(False, False, False, False, False, True, "http")

        # there is only 1 film to import in db
        film_to_import = FilmToImport.objects.get(title="Zaat")

        self.assertEqual(film_to_import.is_imported, True)

        #film is imported
        imported_film = ImportedFilm.objects.get(film__permalink="zaat")

        self.assertEqual(imported_film.film.permalink, "zaat")

        film = Film.objects.get(permalink="zaat")
        self.assertEqual(film.tmdb_import_status, Film.IMPORTED)
        self.assertEqual(film.permalink, "zaat")
        self.assertEqual(film.title, "Zaat")
        self.assertEqual(film.imdb_code, "0072666")

    @integration_test
    def test_tv(self):
        """
           Test case when imdb movie has kind==TV
        """

        self.initialize()
        
        self.client.login(username=self.user.username, password='secret')

        film_to_import = FilmToImport(user = self.user,
                                  title = 'Battlestar Galactica: Razor',
                                  imdb_url = 'http://www.imdb.com/title/tt0991178/',
					              imdb_id='0991178',
                                  status=FilmToImport.ACCEPTED)

        film_to_import.save()

        run(False, False, False, False, False, True, "http")

        # there is only 1 film to import in db
        film_to_import = FilmToImport.objects.get(title="Battlestar Galactica: Razor")

        self.assertEqual(film_to_import.is_imported, True)

        #film is imported
        imported_film = ImportedFilm.objects.get(film__permalink="battlestar-galactica-razor")

        self.assertEqual(imported_film.film.permalink, "battlestar-galactica-razor")

        film = Film.objects.get(permalink="battlestar-galactica-razor")
        self.assertEqual(film.permalink, "battlestar-galactica-razor")
        self.assertEqual(film.title, "Battlestar Galactica: Razor")
        self.assertEqual(film.imdb_code, "0991178")

    @integration_test
    def test_tv_mini_series(self):
        """
           Test case when imdb movie has kind==tv mini-series
        """

        self.initialize()

        self.client.login(username=self.user.username, password='secret')

        film_to_import = FilmToImport(user = self.user,
                                  title = 'Battlestar Galactica',
                                  imdb_url = 'http://www.imdb.com/title/tt0314979/',
					              imdb_id='0314979',
                                  status=FilmToImport.ACCEPTED)

        film_to_import.save()

        run(False, False, False, False, False, True, "http")

        # there is only 1 film to import in db
        film_to_import = FilmToImport.objects.get(title="Battlestar Galactica")

        self.assertEqual(film_to_import.is_imported, True)

        #film is imported
        imported_film = ImportedFilm.objects.get(film__permalink="battlestar-galactica")

        self.assertEqual(imported_film.film.permalink, "battlestar-galactica")

        film = Film.objects.get(permalink="battlestar-galactica")
        self.assertEqual(film.permalink, "battlestar-galactica")
        self.assertEqual(film.title, "Battlestar Galactica")
        self.assertEqual(film.imdb_code, "0314979")

    @integration_test
    def test_gofigure(self):
        """
            Proof that imdb_fetcher is able to fetch TV movie Go Figure
            http://www.imdb.com/title/tt0447987/
        """

        self.initialize()

        self.client.login(username=self.user.username, password='secret')

        film_to_import = FilmToImport(user = self.user,
                                  title = 'Go Figure',
                                  imdb_url = 'http://www.imdb.com/title/tt0447987/',
					              imdb_id='0447987',
                                  status=FilmToImport.ACCEPTED)

        film_to_import.save()

        run(False, False, False, False, False, True, "http")

        # there is only 1 film to import in db
        film_to_import = FilmToImport.objects.get(title="Go Figure")

        self.assertEqual(film_to_import.is_imported, True)

        #film is imported
        imported_film = ImportedFilm.objects.get(film__permalink="go-figure")

        self.assertEqual(imported_film.film.permalink, "go-figure")

        film = Film.objects.get(permalink="go-figure")
        self.assertEqual(film.tmdb_import_status, Film.IMPORTED)
        self.assertEqual(film.permalink, "go-figure")
        self.assertEqual(film.title, "Go Figure")
        self.assertEqual(film.imdb_code, "0447987")

    @integration_test
    def test_many_movies_with_the_same_title(self):
        self. initialize()
        self.client.login(username=self.user.username, password='secret')

        weekend1 = FilmToImport(user = self.user,
                                  title = 'Weekend1',
                                  imdb_url = 'http://www.imdb.com/title/tt1791679/',
					              imdb_id='1791679',
                                  status=FilmToImport.ACCEPTED)

        weekend1.save()

        weekend2 = FilmToImport(user = self.user,
                                  title = 'Weekend2',
                                  imdb_url = 'http://www.imdb.com/title/tt1714210/',
					              imdb_id='1714210',
                                  status=FilmToImport.ACCEPTED)

        weekend2.save()

        weekend3 = FilmToImport(user = self.user,
                                  title = 'Weekend3',
                                  imdb_url = 'http://www.imdb.com/title/tt1910670/',
					              imdb_id='1910670',
                                  status=FilmToImport.ACCEPTED)

        weekend3.save()

        weekend4 = FilmToImport(user = self.user,
                                  title = 'Weekend4',
                                  imdb_url = 'http://www.imdb.com/title/tt0124926/',
					              imdb_id='0124926',
                                  status=FilmToImport.ACCEPTED)

        weekend4.save()

        weekend5 = FilmToImport(user = self.user,
                                  title = 'Weekend5',
                                  imdb_url = 'http://www.imdb.com/title/tt0177364/',
					              imdb_id='0177364',
                                  status=FilmToImport.ACCEPTED)

        weekend5.save()

        weekend6 = FilmToImport(user = self.user,
                                  title = 'Weekend6',
                                  imdb_url = 'http://www.imdb.com/title/tt0145571/',
					              imdb_id='0145571',
                                  status=FilmToImport.ACCEPTED)

        weekend6.save()

        # duplicated IMDB code
        weekend7 = FilmToImport(user = self.user,
                                  title = 'Weekend1',
                                  imdb_url = 'http://www.imdb.com/title/tt1791679/',
					              imdb_id='1791679',
                                  status=FilmToImport.ACCEPTED)

        weekend7.save()

        films_to_import = FilmToImport.objects.all()
        self.assertEqual(films_to_import.count(), 7)

        films_to_import = FilmToImport.objects.filter(is_imported = False, status=FilmToImport.ACCEPTED)
        self.assertEqual(films_to_import.count(), 7)

        run(False, False, False, False, False, True, "http")

        films_to_import = FilmToImport.objects.filter(is_imported = False, status=FilmToImport.ACCEPTED)
        # all films imported
        self.assertEqual(films_to_import.count(), 0)

        imported_films = ImportedFilm.objects.all()
        # imported films
        self.assertEqual(imported_films.count(), 6)

        films = Film.objects.all().order_by('id')
        self.assertEqual(films.count(), 6)
        self.assertEqual(films[0].permalink,'weekend')
        self.assertEqual(films[1].permalink,'weekend-2011')
        self.assertEqual(films[2].permalink,'weekend-2011-1')
        self.assertEqual(films[3].permalink,'weekend-1962')
        self.assertEqual(films[4].permalink,'weekend-1998')
        self.assertEqual(films[5].permalink,'weekend-1998-1')

class ImportPersonTestCase(TestCase):

    user = None

    def clean_data(self):
        User.objects.all().delete()
        Object.objects.all().delete()
        Person.objects.all().delete()
        FilmToImport.objects.all().delete()
        ImportedFilm.objects.all().delete()
        Film.objects.all().delete()

    def initialize(self):
        self.clean_data()

        self.user= User.objects.create_user('michuk', 'borys.musielak@gmail.com', 'secret')
        self.user.save()

    @integration_test
    def duplicate_imdb_code(self):
        """
            ImdbFetcher is trying to save person with imdb_code,
            already existing in db
        """

        self.initialize()

        self.client.login(username=self.user.username, password='secret')

        per = Person()
        per.name = "Jan"
        per.surname = "Kowalski"
        # Schwarzeneger's imdb code
        per.imdb_code = "0000216"
        per.type = Person.TYPE_PERSON
        per.save()
        per = Person.objects.get(imdb_code="0000216")
        self.assertEqual(per.name, "Jan")
        self.assertEqual(per.imdb_code, "0000216")
        
        film_to_import = FilmToImport(user = self.user,
                                  title = 'Terminator',
                                  imdb_url = 'http://www.imdb.com/title/tt0088247/',
					              imdb_id='0088247',
                                  status=FilmToImport.ACCEPTED)
        film_to_import.save()

        run(False, False, False, False, False, True, "http")

        person = Person.objects.get(imdb_code="0000216")
        # duplicate imdb_code - should be set to Schwarzenegger
        self.assertEqual(person.name, "Arnold")
        self.assertEqual(person.surname, "Schwarzenegger")
        self.assertEqual(person.verified_imdb_code, True)
        self.assertEqual(person.imdb_code, "0000216")

        # old imdb_code should be set to None
        per = Person.objects.get(name="Jan", surname="Kowalski")
        self.assertEqual(per.imdb_code, None)

        
    @integration_test
    def unique_imdb_code(self):
        """
            There is a person in db but, he has different imdb_code
        """

        self.initialize()

        self.client.login(username=self.user.username, password='secret')

        per = Person()
        per.name = "Jan"
        per.surname = "Kowalski"
        # Schwarzeneger's imdb code
        per.imdb_code = "0101010101010101"
        per.type = Person.TYPE_PERSON
        per.save()
        per = Person.objects.get(imdb_code="0101010101010101")
        self.assertEqual(per.name, "Jan")
        self.assertEqual(per.imdb_code, "0101010101010101")

        film_to_import = FilmToImport(user = self.user,
                                  title = 'Terminator',
                                  imdb_url = 'http://www.imdb.com/title/tt0088247/',
					              imdb_id='0088247',
                                  status=FilmToImport.ACCEPTED)
        film_to_import.save()

        run(False, False, False, False, False, True, "http")

        person = Person.objects.get(imdb_code="0000216")
        self.assertEqual(person.name, "Arnold")
        self.assertEqual(person.surname, "Schwarzenegger")
        self.assertEqual(person.verified_imdb_code, True)
        self.assertEqual(person.imdb_code, "0000216")

        # old imdb_code should be set to None
        per = Person.objects.get(name="Jan", surname="Kowalski")
        self.assertEqual(per.imdb_code, "0101010101010101")


    @integration_test
    def persons_with_same_name( self ):
        self.initialize()

        fti1 = FilmToImport( user = self.user, title = '180/100',
                imdb_url = 'http://www.imdb.com/title/tt2089598/', imdb_id = '2089598', status = FilmToImport.ACCEPTED )
        fti1.save()

        fti2 = FilmToImport( user = self.user, title = 'The Mad Magician',
                imdb_url = 'http://www.imdb.com/title/tt0047200/', imdb_id = '0047200', status = FilmToImport.ACCEPTED )
        fti2.save()

        run( False, False, False, False, False, True, "http" )

        person = Person.objects.get( imdb_code="3140529" )
        self.assertEqual( person.name, "Éva" )
        self.assertEqual( person.surname, "Gábor" )
        self.assertEqual( person.permalink, "eva-gabor" )
        self.assertEqual( person.verified_imdb_code, True )

        person = Person.objects.get( imdb_code="0001247" )
        self.assertEqual( person.name, "Eva" )
        self.assertEqual( person.surname, "Gabor" )
        self.assertEqual( person.permalink, "eva-gabor-ii" )
        self.assertEqual( person.verified_imdb_code, True )


    @integration_test
    def person_added_manually( self ):
        self.initialize()

        person = Person()
        person.name = "Éva"
        person.surname = "Gábor"
        person.permalink = "eva-gabor"
        person.type = Person.TYPE_PERSON
        person.save()

        self.assertEqual( Person.objects.filter( imdb_code__isnull=True ).count(), 1 )

        fti1 = FilmToImport( user = self.user, title = '180/100',
                imdb_url = 'http://www.imdb.com/title/tt2089598/', imdb_id = '2089598', status = FilmToImport.ACCEPTED )
        fti1.save()

        run( False, False, False, False, False, True, "http" )

        self.assertEqual( Person.objects.filter( imdb_code__isnull=True ).count(), 0 )

        person = Person.objects.get( imdb_code="3140529" )
        self.assertEqual( person.name, "Éva" )
        self.assertEqual( person.surname, "Gábor" )
        self.assertEqual( person.permalink, "eva-gabor" )
        self.assertEqual( person.import_comment, "imdb code assigned automatically" )
        self.assertEqual( person.verified_imdb_code, True )


    @integration_test
    def person_wrong_name( self ):
        self.initialize()

        person = Person()
        person.name = "Ela"
        person.surname = "Gabor"
        person.permalink = "ela-gabor"
        person.imdb_code = "3140529"
        person.verified_imdb_code = True
        person.type = Person.TYPE_PERSON
        person.save()

        fti1 = FilmToImport( user = self.user, title = '180/100',
                imdb_url = 'http://www.imdb.com/title/tt2089598/', imdb_id = '2089598', status = FilmToImport.ACCEPTED )
        fti1.save()

        run( False, False, False, False, False, True, "http" )

        self.assertEqual( Person.objects.filter( imdb_code__isnull=True ).count(), 0 )

        person = Person.objects.get( imdb_code="3140529" )
        self.assertEqual( person.name, "Ela" )
        self.assertEqual( person.surname, "Gabor" )
        self.assertEqual( person.permalink, "ela-gabor" )
        self.assertEqual( person.import_comment, "imdb name: Éva Gábor" )

    @integration_test
    def person_short_imdb_code( self ):
        self.initialize()

        person = Person()
        person.name = "Harrison"
        person.surname = "Ford"
        person.permalink = "harrison-ford"
        person.imdb_code = "148"
        person.type = Person.TYPE_PERSON
        person.save()

        person = Person()
        person.name = "Harrison"
        person.surname = "Ford (II)"
        person.permalink = "harrison-ford-ii"
        person.imdb_code = "0001230"
        person.type = Person.TYPE_PERSON
        person.save()

        self.assertEqual( Person.objects.filter( imdb_code='148' ).count(), 1 )

        fti1 = FilmToImport( user = self.user, title = 'Love in High Gear',
                imdb_url = 'http://www.imdb.com/title/tt0022093/', imdb_id = '0022093', status = FilmToImport.ACCEPTED )
        fti1.save()

        fti2 = FilmToImport( user = self.user, title = 'Journey to shiloh',
                imdb_url = 'http://www.imdb.com/title/tt0063161/', imdb_id = '0063161', status = FilmToImport.ACCEPTED )
        fti2.save()

        fti3 = FilmToImport( user = self.user, title = 'Guys choice Awards 2011',
                imdb_url = 'http://www.imdb.com/title/tt2023505/', imdb_id = '2023505', status = FilmToImport.ACCEPTED )
        fti3.save()

        run( False, False, False, False, False, True, "http" )

        self.assertEqual( Person.objects.filter( name='Harrison', surname__contains='Ford' ).count(), 2 )
        self.assertEqual( Person.objects.filter( imdb_code='148' ).count(), 0 )
        self.assertEqual( Person.objects.get( imdb_code='0000148' ).permalink, 'harrison-ford' )

