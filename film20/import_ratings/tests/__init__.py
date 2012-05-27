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
# Python
import unittest
from haystack.sites import site

# Django
from django.contrib.auth.models import User

# Project
from film20.import_ratings.tests.main import ImportRatingsTestCase
from film20.import_ratings.tests.filmweb import FilmwebImportTestCase
from film20.import_ratings.tests.imdb import IMDBImportTestCase
from film20.import_ratings.tests.criticker import CritickerImportTestCase
from film20.core.models import Rating, Film
from film20.utils.test import TestCase

def suite():
    suite = unittest.TestSuite()

    suite.addTest(ImportRatingsTestCase('test_import_errors'))

    suite.addTest(FilmwebImportTestCase('test_connection'))    
    suite.addTest(FilmwebImportTestCase('test_import'))
    suite.addTest(CritickerImportTestCase('test_import'))
    suite.addTest(IMDBImportTestCase('test_import'))

    return suite
