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
import unittest
import datetime
from decimal import *
from film20.utils.test import TestCase
from film20.showtimes.models import Country, Town, Channel, Screening, \
        FilmOnChannel, TYPE_CINEMA, TYPE_TV_CHANNEL

from django.contrib.auth.models import User
from film20.core.models import Film, Rating, FilmRanking
from film20.useractivity.models import UserActivity
from film20.showtimes.showtimes_helper import get_films_in_cinemas_by_country,\
        get_films_in_tv_by_country


class ShowtimesTestCase(TestCase):
    fixtures = ['test_users.json']

    def setUp(self):
        Film.objects.filter(imdb_code__lt=1000).delete()

    def init_films(self):

        self.f1 = Film(type=1, permalink='przypadek', imdb_code=111, status=1, version=1,
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f1.save()
        self.fc1 = FilmOnChannel(title='fc1', film=self.f1)
        self.fc1.save()
        self.fr1 = FilmRanking(film=self.f1, type=Rating.TYPE_FILM,
                average_score=Decimal('1.0'), number_of_votes=100)
        self.fr1.save()

        self.f2 = Film(type=1, permalink='wrestler', imdb_code=112, status=1, version=1,
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f2.save()
        self.fc2 = FilmOnChannel(title='fc2', film=self.f2)
        self.fc2.save()
        self.fr2 = FilmRanking(film=self.f2, type=Rating.TYPE_FILM,
                average_score=Decimal('2.0'), number_of_votes=100)
        self.fr2.save()

        self.f3 = Film(type=1, permalink='american-history-x', imdb_code=113, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f3.save()
        self.fc3 = FilmOnChannel(title='fc3', film=self.f3)
        self.fc3.save()
        self.fr3 = FilmRanking(film=self.f3, type=Rating.TYPE_FILM,
                average_score=Decimal('3.0'), number_of_votes=100)
        self.fr3.save()

        self.f4 = Film(type=1, permalink='the-big-lebowski', imdb_code=114, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f4.save()
        self.fc4 = FilmOnChannel(title='fc4', film=self.f4)
        self.fc4.save()
        self.fr4 = FilmRanking(film=self.f4, type=Rating.TYPE_FILM,
                average_score=Decimal('4.0'), number_of_votes=100)
        self.fr4.save()

        self.f5 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=115, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f5.save()
        self.fc5 = FilmOnChannel(title='fc5', film=self.f5)
        self.fc5.save()
        self.fr5 = FilmRanking(film=self.f5, type=Rating.TYPE_FILM,
                average_score=Decimal('5.0'), number_of_votes=100)
        self.fr5.save()

        self.f6 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=116, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f6.save()
        self.fc6 = FilmOnChannel(title='fc6', film=self.f6)
        self.fc6.save()
        self.fr6 = FilmRanking(film=self.f6, type=Rating.TYPE_FILM,
                average_score=Decimal('6.0'), number_of_votes=100)
        self.fr6.save()

        self.f7 = Film(type=1, permalink='the-alien', imdb_code=117, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f7.save()
        self.fc7 = FilmOnChannel(title='fc7', film=self.f7)
        self.fc7.save()
        self.fr7 = FilmRanking(film=self.f7, type=Rating.TYPE_FILM,
                average_score=Decimal('7.0'), number_of_votes=100)
        self.fr7.save()

        self.f8 = Film(type=1, permalink='terminator-2-judgment-day', imdb_code=118, status=1, version=1,
        release_year=1991, title='Terminator 2: Judgment Day', popularity=1, popularity_month=1)
        self.f8.save()
        self.fc8 = FilmOnChannel(title='fc8', film=self.f8)
        self.fc8.save()
        self.fr8 = FilmRanking(film=self.f8, type=Rating.TYPE_FILM,
                average_score=Decimal('8.0'), number_of_votes=100)
        self.fr8.save()
        
        self.f9 = Film(type=1, permalink='pulp-fiction', imdb_code=119, status=1, version=1,
        release_year=1991, title='Pulp Fiction', popularity=1, popularity_month=1)
        self.f9.save()
        
        self.f9.save_tags('pulp')

    def initialize(self):
    
        Film.objects.all().delete()

        self.poland = Country.objects.get(code='PL')

        self.init_films()
        self.usa = Country(name='USA', code='US')
        self.usa.save()

        self.new_york = Town(country=self.usa, name='New York',
                has_cinemas=True)
        self.new_york.save()

        self.cinema_ny = Channel(type=TYPE_CINEMA, town=self.new_york, address='Some Street 3')
        self.cinema_ny.save()

        self.hbo = Channel(type=TYPE_TV_CHANNEL, country=self.usa)
        self.hbo.save()

        self.tvp = Channel(type=TYPE_TV_CHANNEL, country=self.poland)
        self.tvp.save()

        time_now = datetime.datetime.utcnow() + datetime.timedelta(0.1)

        self.screen_ny1 = Screening(channel=self.cinema_ny, film=self.fc1,
                utc_time=time_now)
        self.screen_ny1.save()

        self.screen_ny2 = Screening(channel=self.cinema_ny, film=self.fc2,
                utc_time=time_now)
        self.screen_ny2.save()

        self.screen_ny3 = Screening(channel=self.cinema_ny, film=self.fc3,
                utc_time=time_now)
        self.screen_ny3.save()

        self.screen_ny4 = Screening(channel=self.cinema_ny, film=self.fc4,
                utc_time=time_now)
        self.screen_ny4.save()

        self.screen_ny5 = Screening(channel=self.cinema_ny, film=self.fc5,
                utc_time=time_now)
        self.screen_ny5.save()

        self.screen_hbo1 = Screening(channel=self.hbo, film=self.fc1,
                utc_time=time_now)
        self.screen_hbo1.save()

        self.screen_hbo2 = Screening(channel=self.hbo, film=self.fc2,
                utc_time=time_now)
        self.screen_hbo2.save()

        self.screen_hbo3 = Screening(channel=self.hbo, film=self.fc3,
                utc_time=time_now)
        self.screen_hbo3.save()

        self.screen_hbo4 = Screening(channel=self.hbo, film=self.fc4,
                utc_time=time_now)
        self.screen_hbo4.save()

        self.screen_hbo5 = Screening(channel=self.hbo, film=self.fc5,
                utc_time=time_now + datetime.timedelta(8))
        self.screen_hbo5.save()

    def test_get_films_in_cinemas1(self):
        """ Tests situation when there are no showtimes in the given country.
            Takes USA as a default then.
        """

        self.initialize()

        country_films = set([f.id for f in \
                get_films_in_cinemas_by_country(country_code='CR')])
        self.assertTrue(self.f4.id in country_films)

    def test_get_films_in_cinemas2(self):
        """ Tests situation when there are showtimes in the given country.
        """

        self.initialize()
        time_now = datetime.datetime.utcnow() + datetime.timedelta(0.1)

        self.warsaw = Town(country=self.poland, name='Warsaw',
                has_cinemas=True)
        self.warsaw.save()

        self.cinema_ww = Channel(type=TYPE_CINEMA, town=self.warsaw, address='Marszalkowska 2')
        self.cinema_ww.save()

        self.screen_ww1 = Screening(channel=self.cinema_ww, film=self.fc5,
                utc_time=time_now)
        self.screen_ww1.save()

        self.screen_ww2 = Screening(channel=self.cinema_ww, film=self.fc7,
                utc_time=time_now)
        self.screen_ww2.save()

        country_films = set([f.id for f in \
                get_films_in_cinemas_by_country(country_code='PL')])
        self.assertTrue(self.f7.id in country_films)

    def test_get_films_in_tv1(self):
        """
            Tests situation when there are no showtimes in the given country
        """

        self.initialize()

        country_films = set([f.id for f in \
                get_films_in_tv_by_country(country_code='CR')])
        self.assertTrue(self.f1.id in country_films)
        self.assertTrue(self.f4.id in country_films)
        self.assertTrue(self.f5.id not in country_films)

    def test_get_films_in_tv2(self):
        """
            Tests situation when there are showtimes in the given country
        """

        self.initialize()
        time_now = datetime.datetime.utcnow() + datetime.timedelta(0.1)

        self.screen_tvp1 = Screening(channel=self.tvp, film=self.fc1,
                utc_time=time_now)
        self.screen_tvp1.save()

        self.screen_tvp2 = Screening(channel=self.tvp, film=self.fc2,
                utc_time=time_now)
        self.screen_tvp2.save()

        self.screen_tvp3 = Screening(channel=self.tvp, film=self.fc3,
                utc_time=time_now)
        self.screen_tvp3.save()

        self.screen_tvp4 = Screening(channel=self.tvp, film=self.fc4,
                utc_time=time_now)
        self.screen_tvp4.save()

        self.screen_tvp5 = Screening(channel=self.tvp, film=self.fc5,
                utc_time=datetime.datetime.utcnow() + datetime.timedelta(8))
        self.screen_tvp5.save()

        country_films = set([f.id for f in \
                get_films_in_tv_by_country(country_code='PL')])

        self.assertTrue(self.f1.id in country_films)
        self.assertTrue(self.f4.id in country_films)
        self.assertTrue(self.f5.id not in country_films)
    
    def test_double_checkins(self):
        self.initialize()
        
        alice = User.objects.get(username='alice')

        self.screen_hbo1.check_in(alice)
        self.screen_hbo1.check_in(alice)
        self.screen_hbo1.check_in(alice, 2)
        self.screen_hbo1.check_in(alice)

        self.assertEquals(UserActivity.objects.filter(user=alice).count(), 1)

        self.screen_hbo1.film.film.check_in(alice)
        self.screen_hbo1.film.film.check_in(alice)
        self.screen_hbo1.film.film.check_in(alice, 2)
        self.screen_hbo1.film.film.check_in(alice)
        
        self.assertEquals(UserActivity.objects.filter(user=alice).count(), 1)
        
    def test_double_checkins2(self):
        self.initialize()
        
        alice = User.objects.get(username='alice')

        self.screen_hbo1.film.film.check_in(alice)
        self.screen_hbo1.film.film.check_in(alice)
        self.screen_hbo1.film.film.check_in(alice, 2)
        self.screen_hbo1.film.film.check_in(alice)
        self.assertEquals(UserActivity.objects.filter(user=alice).count(), 1)
        
        self.screen_hbo1.check_in(alice)
        self.screen_hbo1.check_in(alice)
        self.screen_hbo1.check_in(alice, 2)
        self.screen_hbo1.check_in(alice)

        self.assertEquals(UserActivity.objects.filter(user=alice).count(), 1)

    def test_activity_message_filter( self ):
        from django.template import Context, Template
        from django.utils.translation import gettext as _
        
        template = Template( '{% load showtimes %}{{ d1|to_checkin_activity_message:d2 }}' )

        now = datetime.datetime.now()

        context = Context( { 'd1': now, 'd2': now } )
        self.assertEqual( template.render( context ), _( 'is watching' ) )

        context = Context( { 'd1': now - datetime.timedelta( hours=1 ), 'd2': now } )
        self.assertEqual( template.render( context ), _( 'is watching' ) )

        context = Context( { 'd1': now + datetime.timedelta( hours=1 ), 'd2': now } )
        self.assertEqual( template.render( context ), _( 'is planing to watch' ) )

        context = Context( { 'd1': now - datetime.timedelta( hours=3 ), 'd2': now } )
        self.assertEqual( template.render( context ), _( 'watched' ) )

    def test_matching(self):
        self.initialize()
        
        foc = FilmOnChannel.objects.match({'title':'pulp fiction'})
        self.assertFalse(foc.film)
        
        foc = FilmOnChannel.objects.match({'title':'pulp,  fiction', 'tag':'pulp'})
        self.assertTrue(foc.film)



