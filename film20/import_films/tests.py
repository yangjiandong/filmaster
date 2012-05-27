# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

from django.test import Client
from film20.utils.test import TestCase, integration_test
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.contrib.auth.models import User, Permission

from film20.core.models import Film, Person
from film20.import_films.models import FilmToImport
from film20.import_films.test_tmdb_fetcher import TmdbPosterFetcherTestCase

class ImportFilmsTestCase( TestCase ):
    def setUp(self):
        self.client = Client( follow=True )

        self.user = User.objects.create_user( "user", "user@user.com", "user" )

        self.mod = User.objects.create_user( "mod", "mod@mod.com", "mod" )
        self.mod.user_permissions.add( Permission.objects.get( codename="can_accept_films" ) )
        self.mod.save()

        Film.objects.filter(imdb_code__lt=1000).delete()

    def tearDown( self ):
        FilmToImport.objects.all().delete()
        User.objects.all().delete()

    @integration_test
    def testImdbCodes( self ):
        from film20.import_films.update_imdb_codes import update_all_imdb_codes

        f1 = Film( type=1, imdb_code="199123", release_year=2008, title="The Incredible Hulk" )
        f1.save()

        f2 = Film( type=1, imdb_code="333332", release_year=1992, title="The Godfather Trilogy: 1901-1980" )
        f2.save()
 
        f3 = Film( type=1, imdb_code="343454", release_year=2007, title="Youth Without Youth" )
        f3.save()

        f4 = Film( type=1, imdb_code="343sd4", release_year=1007, title="Fake Movie" )
        f4.save()

        f5 = Film( type=1, imdb_code="0110413", release_year=1994, title=u"Léon" )
        f5.save()

        f6 = Film( type=1, imdb_code="0289765", release_year=2002, title="Red Dragon" )
        f6.save()

        call_command( 'fix_films_imdb_codes' )

        self.failUnlessEqual( Film.objects.get( pk=f1.pk ).imdb_code, "0800080" )
        self.assertTrue( Film.objects.get( pk=f1.pk ).verified_imdb_code )
        
        self.failUnlessEqual( Film.objects.get( pk=f2.pk ).imdb_code, "0150742" )
        self.assertTrue( Film.objects.get( pk=f2.pk ).verified_imdb_code )

        self.failUnlessEqual( Film.objects.get( pk=f3.pk ).imdb_code, "0481797" )
        self.assertTrue( Film.objects.get( pk=f3.pk ).verified_imdb_code )

        self.failUnlessEqual( Film.objects.get( pk=f4.pk ).imdb_code, "343sd4" )
        self.assertFalse( Film.objects.get( pk=f4.pk ).verified_imdb_code )
        self.assertEqual( Film.objects.get( pk=f4.pk ).import_comment, "nothing matches" )

        self.failUnlessEqual( Film.objects.get( pk=f5.pk ).imdb_code, "0110413" )
        self.assertTrue( Film.objects.get( pk=f5.pk ).verified_imdb_code )

        self.failUnlessEqual( Film.objects.get( pk=f6.pk ).imdb_code, "0289765" )
        self.assertFalse( Film.objects.get( pk=f6.pk ).verified_imdb_code )
        self.assertEqual( Film.objects.get( pk=f6.pk ).import_comment, "too many matching movies: '0289765,0379467'" )



    @integration_test
    def testFixCountries( self ):
        from film20.import_films.update_countries import update_all_films

        f1 = Film( type=1, imdb_code="123", release_year=2002, title="Fake 1",
            production_country_list="FrancePolandGermanyUK," )
        f1.save()

        f2 = Film( type=1, imdb_code="456", release_year=2010, title="Fake 2", 
            production_country_list="USAUKUnited Arab Emirates," )
        f2.save()

        f3 = Film( type=1, imdb_code="789", release_year=2010, title="Fake 3", 
            production_country_list="USA" )
        f3.save()

        f4 = Film( type=1, imdb_code="111", release_year=2010, title="Fake 4", 
            production_country_list="UK, Aasdasd asdas, ," )
        f4.save()

        update_all_films()

        self.failUnlessEqual( Film.objects.get( pk=f1.pk ).production_country_list, 
                       "France,Poland,Germany,UK" )
        self.failUnlessEqual( Film.objects.get( pk=f2.pk ).production_country_list, 
                       "USA,UK,United Arab Emirates" )
        self.failUnlessEqual( Film.objects.get( pk=f3.pk ).production_country_list, 
                       "USA" )
        self.failUnlessEqual( Film.objects.get( pk=f4.pk ).production_country_list, 
                       "UK" )

    @integration_test
    def testNotification( self ):
        from django.core import mail
        from django.contrib.auth.models import User

        from film20.import_films.models import FilmToImport
        from film20.import_films.imdb_fetcher import run

        u1 = User(username='root', email='root@toor.com')
        u1.save()

        f1 = FilmToImport( user = u1, title = 'The Expandables', imdb_url = 'http://www.imdb.com/title/tt1320253/', 
                    imdb_id='1320253', status=FilmToImport.ACCEPTED )
        f1.save()
        
        # clear test outbox
        mail.outbox = []

        run( False, False, False, False, False, True, "http" )
        
        self.assertEqual( len( mail.outbox ), 1 )

        film = Film.objects.get( imdb_code=f1.imdb_id )

        self.assertFalse( "http://fail-test/film" in mail.outbox[0].body )
        self.assertTrue( film.get_absolute_url() in mail.outbox[0].body )

        # try retrive once again
        f1.status=FilmToImport.ACCEPTED
        f1.save()

        mail.outbox = []

        run( False, False, False, False, False, True, "http" )
        
        self.assertEqual( len( mail.outbox ), 1 )
        
        f1 = FilmToImport.objects.get( pk=f1.pk )

        self.assertEqual( f1.status, FilmToImport.ALREADY_IN_DB )
        self.assertTrue( film.get_absolute_url() in mail.outbox[0].body )

    def testModeratorAdd( self ):
        self.client.login( username='mod', password='mod' )
        response = self.client.post( reverse( 'import_film' ), { "imdb_url": "http://www.imdb.com/title/tt0094988/", 
                                                                    "title": "Dekalog 6" })
        
        self.assertEqual( FilmToImport.objects.count(), 1 )

        film_to_import = FilmToImport.objects.all()[0]
        self.assertEqual( film_to_import.status, FilmToImport.ACCEPTED )


    def testRegularUserAdd( self ):
        self.client.login( username='user', password='user' )
        response = self.client.post( reverse( 'import_film' ), { "imdb_url": "http://www.imdb.com/title/tt0094988/", 
                                                                    "title": "Dekalog 6" })
        
        self.assertEqual( FilmToImport.objects.count(), 1 )

        film_to_import = FilmToImport.objects.all()[0]
        self.assertEqual( film_to_import.status, FilmToImport.UNKNOW )


import unittest
from film20.import_films.test_imdb_fetcher import *
from film20.import_films.test_person_fixer import PersonFixerTestCase

def suite():
    suite = unittest.TestSuite()
#    suite.addTest(ImdbFetcherTestCase('test_successfullfetch'))
#    suite.addTest(ImdbFetcherTestCase('test_filmindb'))
#    suite.addTest(ImdbFetcherTestCase('test_tvseries'))

    suite.addTest(ImdbFetcherTestCase('test_tv'))
    suite.addTest(ImdbFetcherTestCase('test_tv_mini_series'))
    suite.addTest(ImdbFetcherTestCase('test_many_movies_with_the_same_title'))
    suite.addTest(ImdbFetcherTestCase('test_gofigure'))
#    suite.addTest(TmdbPosterFetcherTestCase('test_fetch_by_title')) # TODO: move this to integration tests - this is not a unit test
#    suite.addTest(TmdbPosterFetcherTestCase('test_fetch_by_id')) # TODO: move this to integration tests - this is not a unit test
    suite.addTest(TmdbPosterFetcherTestCase('test_tmdb_status'))

    suite.addTest(ImportFilmsTestCase('testImdbCodes'))
    suite.addTest(ImportFilmsTestCase('testFixCountries'))
    suite.addTest(ImportFilmsTestCase('testModeratorAdd'))
    suite.addTest(ImportFilmsTestCase('testRegularUserAdd'))
#    suite.addTest(ImportFilmsTestCase('testNotification')) # uncomment and fix in http://jira.filmaster.org/browse/FLM-1116
#    suite.addTest(ImdbFetcherTestCase('test_posterfetch'))

    suite.addTest( ImportPersonTestCase( 'persons_with_same_name' ) )   
    suite.addTest( ImportPersonTestCase( 'person_added_manually' ) )   
    suite.addTest( ImportPersonTestCase( 'person_wrong_name' ) )   
    suite.addTest( ImportPersonTestCase( 'person_short_imdb_code' ) )   

    suite.addTest( PersonFixerTestCase( 'test_persons' ) )   

    return suite
