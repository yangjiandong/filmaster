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
from film20.recommendations.test_validation import ValidationTestCase
from film20.recommendations.test_queries import QueriesTestCase
from film20.recommendations.test_synopsis import TmdbFetcherTestCase, BotHelperTestCase, WikipediaFetcherTestCase

def suite():
    suite = unittest.TestSuite()
    suite.addTest(ValidationTestCase('test_validate_tags'))
    suite.addTest(QueriesTestCase('test_get_all_ratings'))
    suite.addTest(QueriesTestCase('test_get_recently_popular_films_query'))
#    suite.addTest(QueriesTestCase('test_get_best_psi_films_queryset_alg2'))
    suite.addTest(QueriesTestCase('test_get_best_tci_users'))
    suite.addTest(QueriesTestCase('test_cache_count_ratings'))
    suite.addTest(QueriesTestCase('test_enrich_query_with_tags'))
    suite.addTest(TmdbFetcherTestCase('test_fetcher'))
    suite.addTest(TmdbFetcherTestCase('test_save_searchkeys'))
#    suite.addTest(BotHelperTestCase('test_fetch_synopses_for_films_no_localized_film_nosynopsisindb'))
#    suite.addTest(BotHelperTestCase('test_fetch_synopses_for_films_no_localized_film_onesynopsisindb'))
#    suite.addTest(BotHelperTestCase('test_fetch_synopses_for_films_no_localized_film_twosynopsisindb'))
#    suite.addTest(BotHelperTestCase('test_fetch_synopses_for_films_no_synopses_nolocalizedfilms'))
#    suite.addTest(BotHelperTestCase('test_fetch_synopses_for_films_no_synopses_nolocalizedfilms'))
#    suite.addTest(BotHelperTestCase('test_fetch_synopses_for_films_no_synopses_onelocalizedfilm'))
#    suite.addTest(BotHelperTestCase('test_fetch_synopses_for_films_no_synopses_twolocalizedfilms'))
#    suite.addTest(BotHelperTestCase('test_fetch_synopses_for_films_no_synopses_twolocalizedfilmswithsynopses'))
    suite.addTest(WikipediaFetcherTestCase('test_fetcher'))
    return suite

