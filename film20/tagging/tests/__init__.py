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
from test_commands import CommandsTestCase
from test_translation import TagTranslationTestCase

def suite():
    suite = unittest.TestSuite()

    suite.addTest( TagTranslationTestCase( 'test_command' ) )
    suite.addTest( TagTranslationTestCase( 'test_translation_1' ) )
    suite.addTest( TagTranslationTestCase( 'test_translation_2' ) )
    suite.addTest( TagTranslationTestCase( 'test_translation_3' ) )
    suite.addTest( TagTranslationTestCase( 'test_translation_4' ) )

    suite.addTest( CommandsTestCase( 'test_remove_unused_tags' ) )
    suite.addTest( CommandsTestCase( 'test_duplicate_localized_tags' ) )
    
    return suite
