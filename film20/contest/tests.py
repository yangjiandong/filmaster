#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2010 Filmaster (Borys Musielak, Adam Zielinski).
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
from film20.contest.test_contest import ContestTestCase

def suite():
    suite = unittest.TestSuite()
    
    suite.addTest(ContestTestCase('test_get_current_contest'))
    suite.addTest(ContestTestCase('test_get_contest_by_permalink'))
    suite.addTest(ContestTestCase('test_contest_get_game_for_date'))
    suite.addTest(ContestTestCase('test_contest_get_game_by_permalink'))
    suite.addTest(ContestTestCase('test_get_votes_for_character_in_game'))
    suite.addTest(ContestTestCase('test_voting'))
    suite.addTest(ContestTestCase('test_get_all_games_for_contest'))
#    suite.addTest(ContestTestCase('test_ajax_vote')) # TODO: fix this test before we actually start running contests

    return suite

