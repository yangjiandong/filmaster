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
from django.test.client import Client
from django.contrib.auth.models import User

from film20.core.models import Film, Person, Object, FilmRanking, Rating
from film20.utils.test import TestCase

class RequestTestCase(TestCase):
    fixtures = ['test_users.json']
    def setUp(self):
        self.user = User.objects.get(username='bob')
        self.user.set_password('bob')
        self.user.save()
        
        self.film = Film(type=1, permalink='przypadek', imdb_code=111, status=1, version=1, 
            release_year=1999, title='Przypadek', popularity=1, popularity_month=1)
        self.film.save()
        
        self.person = Person(type=2, permalink='jerzy-stuhr', imdb_code=112, status=1, version=1, 
            name='Jerzy', surname='Stuhr')
        self.person.save()

    
    def test_index(self):
        response = self.client.get('/')
        self.failUnlessEqual(response.status_code, 200)

    def test_film(self):
        response = self.client.get('/film/przypadek/')
        self.failUnlessEqual(response.status_code, 200)

    def test_film_authorized(self):
        self.client.login(username='bob', password='bob')
        response = self.client.get('/film/przypadek/')
        self.assertTrue(response.context['request'].user.is_authenticated())
        self.failUnlessEqual(response.status_code, 200)

    def test_person(self):
        response = self.client.get(self.person.get_absolute_url())
        self.assertEquals(response.status_code, 200)
    
    def test_person_authorized(self):
        self.client.login(username='bob', password='bob')
        response = self.client.get(self.person.get_absolute_url())
        self.assertEquals(response.status_code, 200)

    def tearDown(self):
        Person.objects.all().delete()
        Film.objects.all().delete()

