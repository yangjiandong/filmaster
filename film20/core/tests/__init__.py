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
from test_request import RequestTestCase
from test_templatetags import TemplatetagsTestCase
from test_film_helper import FilmHelperTestCase
# from film20.core.test_rating import RatingTestCase
from test_shortreview import ShortReviewTestCase

import test_user, test_middleware, test_utils, test_rate_films, test_parse_nicknames, test_similar_films

from test_rate_films import RateFilmsTestCase
from test_paginator import PaginatorTestCase

def suite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTest(RateFilmsTestCase('test_rate_films2'))
    suite.addTest(RateFilmsTestCase('test_rating_useractivity'))
    suite.addTest(RateFilmsTestCase('test_anonymous_rating'))
    
    suite.addTest(RequestTestCase('test_index'))
    suite.addTest(RequestTestCase('test_person'))
    suite.addTest(RequestTestCase('test_film'))
    suite.addTest(RequestTestCase('test_person_authorized'))
    suite.addTest(RequestTestCase('test_film_authorized'))
    suite.addTest(TemplatetagsTestCase('test_sanitize'))
    suite.addTest(TemplatetagsTestCase('test_truncatechars'))
    suite.addTest(TemplatetagsTestCase('test_poster'))
    suite.addTest(TemplatetagsTestCase('test_human_readable_date'))
    suite.addTest(FilmHelperTestCase('test_get_related_localized_objects'))
    suite.addTest(FilmHelperTestCase('test_get_related_localized_objects'))
    suite.addTest(TemplatetagsTestCase('test_allowed_tags'))
    suite.addTest(ShortReviewTestCase('test_saving_single_shortreview'))
    suite.addTest(ShortReviewTestCase('test_delete_single_shortreview'))
    suite.addTest(ShortReviewTestCase('test_edit_single_shortreview'))
    suite.addTest(ShortReviewTestCase('test_saving_double_shortreviews'))
    suite.addTest(ShortReviewTestCase('test_saving_wall_post'))
    suite.addTest(TemplatetagsTestCase('test_filmaster_recommends'))
    
    suite.addTests(loader.loadTestsFromModule(test_user))
    suite.addTests(loader.loadTestsFromModule(test_middleware))
    suite.addTests(loader.loadTestsFromModule(test_utils))
    suite.addTests(loader.loadTestsFromModule(test_paginator))
    suite.addTests(loader.loadTestsFromModule(test_parse_nicknames))
    suite.addTests(loader.loadTestsFromModule(test_similar_films))
    

    suite.addTest(PaginatorTestCase('test_inf_paginator'))
    return suite
