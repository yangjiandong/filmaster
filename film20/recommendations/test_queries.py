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
from django.utils import unittest
from django.contrib.auth.models import User, Permission
from film20.core.models import Object, Film, FilmLog, Rating, Recommendation, Person
from film20.add_films.models import AddedCharacter, AddedFilm
from film20.recommendations.recom_helper import RecomHelper
from film20.recommendations.bot_helper import do_create_comparators 
from film20.import_ratings.import_ratings_helper import save_rating

from film20.core import rating_helper
from film20.core.film_helper import FilmHelper
from film20.core.rating_form import RatingForm
from film20.utils.test import TestCase, is_postgres

class QueriesTestCase(TestCase):

    def setUp(self):
        User.objects.all().delete()

        Object.objects.all().delete()
        Film.objects.all().delete()
        FilmLog.objects.all().delete()
        Rating.objects.all().delete()
        Recommendation.objects.all().delete()
        Person.objects.all().delete()

        AddedCharacter.objects.all().delete()
        AddedFilm.objects.all().delete()

        # set up users
        self.u1 = User(username='first', email='first@filmaster.com')
        self.u1.save()

        self.u2 = User.objects.create_user( "root", "root@root.com", "root" )
        self.u2.user_permissions.add( Permission.objects.get( codename="can_accept_added_films" ) )
        self.u2.save()

        self.u3=User(username='third', email='third@man.com')
        self.u3.save()

        self.u4=User(username='fourth', email='fourth@kind.com')
        self.u4.save()

        self.u5=User(username='fifth', email='fifth@element.com')
        self.u5.save()

        self.u6=User(username='sixth', email='sixth@sense.com')
        self.u6.save()

        # some persons
        self.p1 = Person(name="Clint", surname="Eastwood", imdb_code=None, type=Person.TYPE_PERSON)
        self.p1.save()

        self.p2 = Person(name="Sylvester", surname="Stallone", imdb_code=None, type=Person.TYPE_PERSON)
        self.p2.save()

        self.p3 = Person(name="Jack", surname="Mort", imdb_code=None, type=Person.TYPE_PERSON)
        self.p3.save()

        # set up films
        self.f1 = Film(type=1, permalink='przypadek', imdb_code=111, status=1, version=1, 
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f1.save()

        self.f2 = Film(type=1, permalink='wrestler', imdb_code=112, status=1, version=1, 
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f2.save()

        self.f3 = Film(type=1, permalink='american-history-x', imdb_code=113, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f3.save()

        self.f4 = Film(type=1, permalink='the-big-lebowski', imdb_code=114, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f4.save()

        self.f5 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=115, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f5.save()

        self.f6 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=116, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f6.save()

        self.f7 = Film(type=1, permalink='the-alien', imdb_code=117, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f7.save()

        self.f8 = Film(type=1, permalink='terminator-2-judgment-day', imdb_code=118, status=1, version=1,
        release_year=1991, title='Terminator 2: Judgment Day', popularity=1, popularity_month=1)
        self.f8.save()

        self.f9 = Film(type=1, permalink='przypadek', imdb_code=119, status=1, version=1, 
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f9.save()

        self.f10 = Film(type=1, permalink='wrestler', imdb_code=120, status=1, version=1, 
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f10.save()

        self.f11 = Film(type=1, permalink='american-history-x', imdb_code=121, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f11.save()

        self.f12 = Film(type=1, permalink='the-big-lebowski', imdb_code=122, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f12.save()

        self.f13 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=123, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f13.save()

        self.f14 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=124, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f14.save()

        self.f15 = Film(type=1, permalink='the-alien', imdb_code=125, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f15.save()

        self.f16 = Film(type=1, permalink='przypadek', imdb_code=126, status=1, version=1, 
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f16.save()

        self.f17 = Film(type=1, permalink='wrestler', imdb_code=127, status=1, version=1, 
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f17.save()

        self.f18 = Film(type=1, permalink='american-history-x', imdb_code=128, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f18.save()

        self.f19 = Film(type=1, permalink='the-big-lebowski', imdb_code=129, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f19.save()

        self.f20 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=130, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f20.save()

        self.f21 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=131, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f21.save()

        self.f22 = Film(type=1, permalink='the-alien', imdb_code=132, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f22.save()

        self.f23 = Film(type=1, permalink='terminator-2-judgment-day', imdb_code=133, status=1, version=1,
        release_year=1991, title='Terminator 2: Judgment Day', popularity=1, popularity_month=1)
        self.f23.save()

        self.f24 = Film(type=1, permalink='przypadek', imdb_code=134, status=1, version=1, 
            release_year=1999, title='Przypadek', popularity=20, popularity_month=10)
        self.f24.save()

        self.f25 = Film(type=1, permalink='wrestler', imdb_code=135, status=1, version=1, 
            release_year=2008, title='Wrestler', popularity=10, popularity_month=1)
        self.f25.save()

        self.f26 = Film(type=1, permalink='american-history-x', imdb_code=136, status=1, version=1,
            release_year=1998, title='American History X', popularity=1, popularity_month=1)
        self.f26.save()

        self.f27 = Film(type=1, permalink='the-big-lebowski', imdb_code=137, status=1, version=1,
            release_year=1998, title='The Big Lebowski', popularity=1, popularity_month=1)
        self.f27.save()

        self.f28 = Film(type=1, permalink='the-lord-of-the-rings-the-fellowship-of-the-ring', imdb_code=138, status=1, version=1,
            release_year=2001, title='The Lord of the Rings: The Fellowship of the Ring', popularity=1, popularity_month=1)
        self.f28.save()

        self.f29 = Film(type=1, permalink='raiders-of-the-lost-ark', imdb_code=139, status=1, version=1,
            release_year=1981, title='Raiders of the Lost Ark', popularity=1, popularity_month=1)
        self.f29.save()

        self.f30 = Film(type=1, permalink='the-alien', imdb_code=140, status=1, version=1,
            release_year=1979, title='The Alien', popularity=1, popularity_month=1)
        self.f30.save()

        self.f31 = AddedFilm(title = 'Added film part 1', localized_title='Added film PL', release_year = 2010, user = self.u1)
        self.f31.save()

        self.f31.directors.add(self.p1)
        self.f31.save()

        AddedCharacter.objects.create(added_film=self.f31, person=self.p3, character="Jack Mort")

        self.f31.accept(self.u2)
	
        self.f32 = AddedFilm(title = 'Added film part 2', localized_title='Added film PL', release_year = 2010, user = self.u1)
        self.f32.save()

        self.f32.directors.add(self.p2)
        self.f32.save()

        AddedCharacter.objects.create(added_film=self.f32, person=self.p3, character="Jack Mort")

        self.f32.accept(self.u2)

        #tagging
        self.f1.save_tags('comedy drama horror animation mystery')
        self.f2.save_tags('comedy sci-fi thriller series')
        self.f3.save_tags('comedy')
        self.f4.save_tags('sci-fi')
        self.f5.save_tags('horror')
        self.f6.save_tags('thriller')
        self.f7.save_tags('drama')
        self.f8.save_tags('series')
        self.f9.save_tags('sci-fi')
        self.f10.save_tags('fantasy')
        self.f11.save_tags('mystery')
        self.f12.save_tags('action')
        self.f13.save_tags('adventure')
        self.f14.save_tags('animation')
        self.f15.save_tags('family')
        self.f16.save_tags('thriller')
        self.f17.save_tags('drama')
        self.f18.save_tags('series')
        self.f19.save_tags('sci-fi')
        self.f20.save_tags('fantasy')
        self.f21.save_tags('comedy')
        self.f22.save_tags('animation')
        self.f23.save_tags('comedy')
        self.f24.save_tags('sci-fi')
        self.f25.save_tags('horror')
        self.f26.save_tags('thriller')
        self.f27.save_tags('drama')
        self.f28.save_tags('series')
        self.f29.save_tags('sci-fi')
        self.f30.save_tags('fantasy')

        #First user ratings
        save_rating(self.f1, self.u1, 1)
        save_rating(self.f2, self.u1, 2)
        save_rating(self.f3, self.u1, 3)
        save_rating(self.f4, self.u1, 4)
        save_rating(self.f5, self.u1, 5)
        save_rating(self.f6, self.u1, 6)
        save_rating(self.f7, self.u1, 7)
        save_rating(self.f8, self.u1, 8)
        save_rating(self.f9, self.u1, 9)
        save_rating(self.f10, self.u1, 10)
        save_rating(self.f11, self.u1, 1)
        save_rating(self.f12, self.u1, 2)
        save_rating(self.f13, self.u1, 3)
        save_rating(self.f14, self.u1, 4)
        save_rating(self.f15, self.u1, 5)
        save_rating(self.f16, self.u1, 6)
        save_rating(self.f17, self.u1, 7)
        save_rating(self.f18, self.u1, 8)
        save_rating(self.f19, self.u1, 9)
        save_rating(self.f20, self.u1, 10)
        save_rating(self.f21, self.u1, 1)
        save_rating(self.f22, self.u1, 2)
        save_rating(self.f23, self.u1, 3)
        save_rating(self.f24, self.u1, 4)
        save_rating(self.f25, self.u1, 5)
        save_rating(self.f26, self.u1, 6)
        save_rating(self.f27, self.u1, 7)
        save_rating(self.f28, self.u1, 8)
        save_rating(self.f29, self.u1, 9)
        save_rating(self.f30, self.u1, 10)             

        #Second user ratings - more than minimal common films requirement (15)
        save_rating(self.f1, self.u2, 1)
        save_rating(self.f2, self.u2, 2)
        save_rating(self.f3, self.u2, 3)
        save_rating(self.f4, self.u2, 4)
        save_rating(self.f5, self.u2, 5)
        save_rating(self.f6, self.u2, 6)
        save_rating(self.f7, self.u2, 7)
        save_rating(self.f8, self.u2, 8)
        save_rating(self.f9, self.u2, 9)
        save_rating(self.f10, self.u2, 10)
        save_rating(self.f11, self.u2, 1)
        #save_rating(self.f12, self.u2, 2)
        save_rating(self.f13, self.u2, 3)
        #save_rating(self.f14, self.u2, 4)
        save_rating(self.f15, self.u2, 5)
        #save_rating(self.f16, self.u2, 6)
        save_rating(self.f17, self.u2, 7)
        #save_rating(self.f18, self.u2, 8)
        save_rating(self.f19, self.u2, 9)
        #save_rating(self.f20, self.u2, 10)
        save_rating(self.f21, self.u2, 1)
        #save_rating(self.f22, self.u2, 2)
        save_rating(self.f23, self.u2, 3)
        #save_rating(self.f24, self.u2, 4)
        save_rating(self.f25, self.u2, 5)
        #save_rating(self.f26, self.u2, 6)
        save_rating(self.f27, self.u2, 7)
        #save_rating(self.f28, self.u2, 8)
        save_rating(self.f29, self.u2, 9)
        #save_rating(self.f30, self.u2, 10)             

        # Third user ratings - equal with minimal common films requirement (15)
        #save_rating(self.f1, self.u3, 1)
        #save_rating(self.f2, self.u3, 2)
        #save_rating(self.f3, self.u3, 3)
        #save_rating(self.f4, self.u3, 4)
        #save_rating(self.f5, self.u3, 5)
        #save_rating(self.f6, self.u3, 6)
        #save_rating(self.f7, self.u3, 7)
        #save_rating(self.f8, self.u3, 8)
        #save_rating(self.f9, self.u3, 9)
        #save_rating(self.f10, self.u3, 10)
        #save_rating(self.f11, self.u3, 1)
        #save_rating(self.f12, self.u3, 2)
        #save_rating(self.f13, self.u3, 3)
        #save_rating(self.f14, self.u3, 4)
        #save_rating(self.f15, self.u3, 5)
        save_rating(self.f16, self.u3, 6)
        save_rating(self.f17, self.u3, 7)
        save_rating(self.f18, self.u3, 8)
        save_rating(self.f19, self.u3, 9)
        save_rating(self.f20, self.u3, 10)
        save_rating(self.f21, self.u3, 1)
        save_rating(self.f22, self.u3, 2)
        save_rating(self.f23, self.u3, 3)
        save_rating(self.f24, self.u3, 4)
        save_rating(self.f25, self.u3, 5)
        save_rating(self.f26, self.u3, 6)
        save_rating(self.f27, self.u3, 7)
        save_rating(self.f28, self.u3, 8)
        save_rating(self.f29, self.u3, 9)
        save_rating(self.f30, self.u3, 10)             

        # Fourth user ratings - less than minimal films requirement
        #save_rating(self.f1, self.u4, 1)
        #save_rating(self.f2, self.u4, 2)
        #save_rating(self.f3, self.u4, 3)
        #save_rating(self.f4, self.u4, 4)
        #save_rating(self.f5, self.u4, 5)
        #save_rating(self.f6, self.u4, 6)
        #save_rating(self.f7, self.u4, 7)
        #save_rating(self.f8, self.u4, 8)
        #save_rating(self.f9, self.u4, 9)
        #save_rating(self.f10, self.u4, 10)
        #save_rating(self.f11, self.u4, 1)
        #save_rating(self.f12, self.u4, 2)
        #save_rating(self.f13, self.u4, 3)
        #save_rating(self.f14, self.u4, 4)
        #save_rating(self.f15, self.u4, 5)
        #save_rating(self.f16, self.u4, 6)
        #save_rating(self.f17, self.u4, 7)
        #save_rating(self.f18, self.u4, 8)
        #save_rating(self.f19, self.u4, 9)
        #save_rating(self.f20, self.u4, 10)
        save_rating(self.f21, self.u4, 1)
        save_rating(self.f22, self.u4, 2)
        save_rating(self.f23, self.u4, 3)
        save_rating(self.f24, self.u4, 4)
        save_rating(self.f25, self.u4, 5)
        save_rating(self.f26, self.u4, 6)
        save_rating(self.f27, self.u4, 7)
        save_rating(self.f28, self.u4, 8)
        save_rating(self.f29, self.u4, 9)
        save_rating(self.f30, self.u4, 10)             

        # Fifth user ratings - the same films rated (1st and 5th user) but different
        # ratings
        #save_rating(self.f1, self.u5, 10)
        #save_rating(self.f2, self.u5, 9)
        #save_rating(self.f3, self.u5, 8)
        #save_rating(self.f4, self.u5, 7)
        #save_rating(self.f5, self.u5, 6)
        #save_rating(self.f6, self.u5, 5)
        #save_rating(self.f7, self.u5, 4)
        #save_rating(self.f8, self.u5, 3)
        #save_rating(self.f9, self.u5, 2)
        #save_rating(self.f10, self.u5, 1)
        #save_rating(self.f11, self.u5, 10)
        #save_rating(self.f12, self.u5, 9)
        #save_rating(self.f13, self.u5, 8)
        #save_rating(self.f14, self.u5, 7)
        #save_rating(self.f15, self.u5, 6)
        #save_rating(self.f16, self.u5, 5)
        #save_rating(self.f17, self.u5, 4)
        #save_rating(self.f18, self.u5, 3)
        #save_rating(self.f19, self.u5, 2)
        #save_rating(self.f20, self.u5, 1)
        #save_rating(self.f21, self.u5, 10)
        #save_rating(self.f22, self.u5, 9)
        #save_rating(self.f23, self.u5, 8)
        #save_rating(self.f24, self.u5, 7)
        #save_rating(self.f25, self.u5, 6)
        #save_rating(self.f26, self.u5, 5)
        #save_rating(self.f27, self.u5, 4)
        #save_rating(self.f28, self.u5, 3)
        #save_rating(self.f29, self.u5, 2)
        #save_rating(self.f30, self.u5, 1)             

        # Sixth user ratings - the same films rated (1st and 5th user) but different
        # ratings
        save_rating(self.f1, self.u6, 10)
        save_rating(self.f2, self.u6, 10)
        save_rating(self.f3, self.u6, 10)
        save_rating(self.f4, self.u6, 10)
        save_rating(self.f5, self.u6, 10)
        save_rating(self.f6, self.u6, 10)
        save_rating(self.f7, self.u6, 10)
        save_rating(self.f8, self.u6, 10)
        save_rating(self.f9, self.u6, 10)
        save_rating(self.f10, self.u6, 10)
        save_rating(self.f11, self.u6, 10)
        save_rating(self.f12, self.u6, 10)
        save_rating(self.f13, self.u6, 10)
        save_rating(self.f14, self.u6, 10)
        save_rating(self.f15, self.u6, 10)
        save_rating(self.f16, self.u6, 10)
        save_rating(self.f17, self.u6, 10)
        save_rating(self.f18, self.u6, 10)
        save_rating(self.f19, self.u6, 10)
        save_rating(self.f20, self.u6, 10)
        save_rating(self.f21, self.u6, 10)
        save_rating(self.f22, self.u6, 10)
        save_rating(self.f23, self.u6, 10)
        save_rating(self.f24, self.u6, 10)
        save_rating(self.f25, self.u6, 10)
        save_rating(self.f26, self.u6, 10)
        save_rating(self.f27, self.u6, 10)
        save_rating(self.f28, self.u6, 10)
        save_rating(self.f29, self.u6, 10)
        save_rating(self.f30, self.u6, 10)             

    @unittest.skipIf(not is_postgres, "sqlite is not supported yet")
    def test_get_recently_popular_films_query(self):
        print "Test get recently popular films query"
        """
           Test for query which gets the most popular films for the rating machine.
           First it should return all films, then we rate one and in the second call
           it should only retrieve the other film.
        """

        recom_helper = RecomHelper()
        film_helper = FilmHelper()

        u1_result = recom_helper.get_recently_popular_films_query(self.u1.id)
        self.assertEquals(len(u1_result), 2)

        u2_result = recom_helper.get_recently_popular_films_query(self.u2.id)
        self.assertEquals(len(u2_result), 12)

        film_with_director_and_actor = Film.objects.filter(title__startswith="Added film part 1")
        related_directors = film_helper.get_film_directors(film_with_director_and_actor[0])
        related_characters = film_helper.get_film_actors(film_with_director_and_actor[0])
        related_actors = []
        for character in related_characters:
            actor = character.person
            related_actors.append(actor)

        POST = {}
        # TODO check why it starts breaking (form invalid) when form_id is set
        #POST['form_id'] = '1'
        POST['rating'] = '6'
        POST['object_id'] = str(self.f12.parent.id)
        POST['form_type'] = str(Rating.TYPE_FILM)
        POST['cancel_rating'] = '0'
        rating_form = RatingForm(POST)
        if rating_form.is_valid():
            rating_helper.add_edit_rating(rating_form, self.u2)
        else:
            print "RATING FORM INVALID!"

        result = recom_helper.get_recently_popular_films_query(self.u2.id)
        self.assertEquals(len(result), 11)

        # test filtering
        result = recom_helper.get_recently_popular_films_query(self.u5.id)
        self.assertEquals(len(result), 32)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, year_from='1990')
        self.assertEquals(len(result), 24)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, year_to='2000')
        self.assertEquals(len(result), 22)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, year_from='1990', year_to='2000')
        self.assertEquals(len(result), 14)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, popularity='10')
        self.assertEquals(len(result), 8)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, year_from='1990', year_to='2000', popularity='10')
        self.assertEquals(len(result), 4)

        rated_films = [self.f1.id, self.f3.id, self.f5.id, self.f7.id, self.f9.id]
        result = recom_helper.get_recently_popular_films_query(self.u5.id, rated_films=rated_films)
        self.assertEquals(len(result), 27)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, year_from='1990', year_to='2000', rated_films=rated_films, popularity='10')
        self.assertEquals(len(result), 2)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, related_director=related_directors)
        self.assertEquals(len(result), 1)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, related_actor=related_actors)
        self.assertEquals(len(result), 2)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, related_director=related_directors, related_actor=related_actors)
        self.assertEquals(len(result), 1)

        result = recom_helper.get_recently_popular_films_query(self.u5.id, year_from='1990', year_to='2011', related_director=related_directors, related_actor=related_actors)
        self.assertEquals(len(result), 1)

#    @unittest.skipIf(not is_postgres, "postgres dependend")
#    def test_get_best_psi_films_queryset_alg2(self):
#        """
#           Test for query that retrieves top recommendations.
#           First it should return all films, then we rate one and in the second call
#           it should only retrieve the other film.
#        """
#
#        recom_helper = RecomHelper()
#        film_helper = FilmHelper()
#
#        # no recommendations yet, the result should be 0
#        result = recom_helper.get_best_psi_films_queryset_alg2(self.u4.id)
#        self.assertEquals(len(result), 0)
#
#        # simulate generating recommendations (for all films) and test again, it should retrieve all films
#        r1 = Recommendation()
#        r1.guess_rating_alg2 = 7
#        r1.film = self.f19
#        r1.user = self.u4
#        r1.save()
#        r2 = Recommendation()
#        r2.guess_rating_alg2 = 8
#        r2.film = self.f20
#        r2.user = self.u4
#        r2.save()
#        result = recom_helper.get_best_psi_films_queryset_alg2(self.u4.id)
#        self.assertEquals(len(result), 2)
#
#        # rate one film, it should be removed from the list
#        POST = {}
#       # TODO check why it starts breaking (form invalid) when form_id is set
#       #POST['form_id'] = '1'
#       POST['rating'] = '6'
#       POST['object_id'] = str(self.f20.parent.id)
#       POST['form_type'] = str(Rating.TYPE_FILM)
#       POST['cancel_rating'] = '0'
#       rating_form = RatingForm(POST)
#       if rating_form.is_valid():
#           rating_helper.add_edit_rating(rating_form, self.u4)
#       else:
#           print "RATING FORM INVALID!"
#
#        result = recom_helper.get_recently_popular_films_query(self.u4.id)
#        self.assertEquals(len(result), 21)

    @unittest.skip("temporary disabled")
    def test_get_best_tci_users(self):
        """
           Test for query that retrieves top users (based on common taste).
        """
        do_create_comparators()
        recom_helper = RecomHelper()
        result = recom_helper.get_best_tci_users(self.u1)
        print "result -->", result
        self.assertEquals(len(result), 4) 

    def test_enrich_query_with_tags(self):
        print "Test enrich query with tags"
        recom_helper = RecomHelper()
        film_helper = FilmHelper()

        comedies = recom_helper.get_films_for_tag('comedy')
        scifis = recom_helper.get_films_for_tag('sci-fi')
        horrors = recom_helper.get_films_for_tag('horror')
        thrillers = recom_helper.get_films_for_tag('thriller')
        dramas = recom_helper.get_films_for_tag('drama')
        fantasies = recom_helper.get_films_for_tag('fantasy')
        mysteries = recom_helper.get_films_for_tag('mystery')
        animations = recom_helper.get_films_for_tag('animation')
        series = recom_helper.get_films_for_tag('series')

        self.assertEquals(len(comedies), 5)
        self.assertEquals(len(scifis), 6)
        self.assertEquals(len(horrors), 3)
        self.assertEquals(len(thrillers), 4)
        self.assertEquals(len(dramas), 4)
        self.assertEquals(len(fantasies), 3)
        self.assertEquals(len(mysteries), 2)
        self.assertEquals(len(animations), 3)
        self.assertEquals(len(series), 4)

    def test_get_all_ratings(self):
        recom_helper = RecomHelper()
        film_helper = FilmHelper()

        film_with_director_and_actor = Film.objects.filter(title__startswith="Added film part 2")
        related_directors = film_helper.get_film_directors(film_with_director_and_actor[0])
        related_characters = film_helper.get_film_actors(film_with_director_and_actor[0])
        related_actors = []
        for character in related_characters:
            actor = character.person
            related_actors.append(actor)

        non_rated_films = Film.objects.filter(rating__isnull=True, title__startswith="Added")
        
        POST = {}
        #POST['form_id'] = '1'
        POST['rating'] = '6'
        POST['object_id'] = str(non_rated_films[1].parent.id)
        POST['form_type'] = str(Rating.TYPE_FILM)
        POST['cancel_rating'] = '0'
        rating_form = RatingForm(POST)
        if rating_form.is_valid():
            rating_helper.add_edit_rating(rating_form, self.u1)
        else:
            print "RATING FORM INVALID!"

        all_ratings = recom_helper.get_all_ratings(self.u1.id)
        self.assertEquals(len(all_ratings), 31)
        
        director_ratings = recom_helper.get_all_ratings(self.u1.id, related_director=related_directors)
        self.assertEquals(len(director_ratings), 1)
        
        actor_ratings = recom_helper.get_all_ratings(self.u1.id, related_actor=related_actors)
        self.assertEquals(len(actor_ratings), 1)
        
        from_ratings = recom_helper.get_all_ratings(self.u1.id, year_from = 1990)
        self.assertEquals(len(from_ratings), 23)
        
        to_ratings = recom_helper.get_all_ratings(self.u1.id, year_to = 2000)
        self.assertEquals(len(to_ratings), 22)
        
        popularity_ratings = recom_helper.get_all_ratings(self.u1.id, popularity = 5)
        self.assertEquals(len(popularity_ratings), 8)

        tag_ratings = recom_helper.get_all_ratings(self.u1.id, tags='comedy')
        self.assertEquals(len(tag_ratings), 5)

    def test_cache_count_ratings(self):
        recom_helper = RecomHelper()
        ratings_count = recom_helper.count_ratings(self.u3.id)
        self.assertEquals(ratings_count, 15)

        save_rating(self.f1, self.u3, 1)
        ratings_count = recom_helper.count_ratings(self.u3.id)
        self.assertEquals(ratings_count, 16)

    def tearDown(self):
        User.objects.all().delete()

        Object.objects.all().delete()
        Film.objects.all().delete()
        FilmLog.objects.all().delete()
        Rating.objects.all().delete()
        Recommendation.objects.all().delete()
        Person.objects.all().delete()

        AddedCharacter.objects.all().delete()
        AddedFilm.objects.all().delete()
