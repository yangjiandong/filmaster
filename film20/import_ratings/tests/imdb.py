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
import unittest, os

from django.test.client import Client
from film20.core.models import Rating,Film,User
from film20.import_ratings.models import save_ratings_in_db
from film20.import_ratings.import_ratings_helper import *
from film20.import_ratings.tests.imports import ImportTestCase
from film20.utils.test import integration_test

class IMDBImportTestCase(ImportTestCase):
    @integration_test
    def test_import(self):
        """
            Import a sample voting history from Filmweb
        """                

        f = open('import_ratings/tests/test_data/imdb_ratings.csv', 'rb')
        ratings_list = parse_imdb_votes(f)

        self.assertEquals(len(ratings_list), 5)

        save_ratings_in_db(self.u1, ratings_list, ImportRatings.IMDB, overwrite=True)

        all_ratings = ImportRatings.objects.all()
        self.assertEquals(len(all_ratings), 1)

        import_ratings()

        ratingsLogs = ImportRatingsLog.objects.all()
        self.assertEquals(len(ratingsLogs), 1)
        print ratingsLogs[0]

        ratings = Rating.objects.all()
        self.assertEquals(len(ratings), 5)
