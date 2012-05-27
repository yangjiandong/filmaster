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
from film20.useractivity.test_watching import WatchingTestCase
from film20.useractivity.test_activities import UserActivityTestCase
from film20.useractivity.test_widgets import WidgetsTest

def suite():
    suite = unittest.TestSuite()
    suite.addTest(UserActivityTestCase('test_saving_post_activity'))
    suite.addTest(UserActivityTestCase('test_updating_post_activity'))
    suite.addTest(UserActivityTestCase('test_saving_shortreview_activity'))
    suite.addTest(UserActivityTestCase('test_updating_shortreview_activity'))
    suite.addTest(UserActivityTestCase('test_saving_externallink_activity'))
    suite.addTest(UserActivityTestCase('test_saving_comment_activity'))
    suite.addTest(UserActivityTestCase('test_updating_comment_activity'))
    suite.addTest(UserActivityTestCase('test_saving_draft_post_activity'))
    suite.addTest(UserActivityTestCase('test_deleting_post_activity'))
    suite.addTest(UserActivityTestCase('test_updating_relatedfilm_post_activity'))
    suite.addTest(UserActivityTestCase('test_rating_activity'))
#    suite.addTest(UserActivityTestCase('test_planet_tag')) # deprecated for now
    suite.addTest(WidgetsTest('test_latest_checkins'))
    suite.addTest(WidgetsTest('test_latest_ratings')) # TODO: fix in http://jira.filmaster.org/browse/FLM-1118
    suite.addTest(WatchingTestCase('test_watching_subscribe'))
    suite.addTest(WatchingTestCase('test_watching_notification')) # TODO: fix in http://jira.filmaster.org/browse/FLM-1116
    return suite

