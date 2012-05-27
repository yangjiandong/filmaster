#-*- coding: utf-8 -*-
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
import os

from django.utils import unittest
from django.test.client import Client
from django.contrib.auth.models import User

from film20.import_ratings.import_ratings_helper import FilmwebRatingsFetcher 
from film20.import_ratings.import_ratings_helper import parse_criticker_votes
from film20.import_ratings.models import save_ratings_in_db
from film20.import_ratings.import_ratings_helper import import_ratings
from film20.core.models import Rating, Film
from film20.import_ratings.models import ImportRatings, ImportRatingsLog
from film20.import_ratings.tests.imports import ImportTestCase
from django.conf import settings

from film20.utils.test import integration_test

class FilmwebImportTestCase(ImportTestCase):

    @integration_test
    def test_connection(self):
        frf = FilmwebRatingsFetcher(self.u1, "dasm", "filmweb", kind=ImportRatings.FILMWEB, overwrite=True)
        self.assertEqual(frf.user_id, "1824604")

        path = os.path.dirname('')
        votes_url = os.path.abspath('import_ratings/tests/test_data/filmweb_dasm.txt')
        votes_file = open(votes_url, 'rb')
        
        self.maxDiff = None
        self.assertMultiLineEqual(unicode(frf.votes_url), unicode(votes_file.read()))

    @integration_test
    def test_import(self):
        """
            Import a sample voting history from Filmweb
        """
        path = os.path.dirname('')
        votes_url = os.path.abspath('import_ratings/tests/test_data/filmweb_rankings.txt')
        votes_file = open(votes_url, 'rb')
        frf = FilmwebRatingsFetcher(self.u1, "dasm", "filmweb", kind=ImportRatings.FILMWEB, overwrite=True, votes_url=votes_file.read())
        
        all_ratings = ImportRatings.objects.all()
        self.assertEquals(len(all_ratings), 1)

        import_ratings()

        ratingsLogs = ImportRatingsLog.objects.all()
        self.assertEquals(len(ratingsLogs), 1)

        ratings = Rating.objects.all()
        self.assertEquals(len(ratings), 4)
