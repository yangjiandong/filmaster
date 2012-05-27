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
import unittest
from film20.recommendations.forms import validate_tags
from film20.utils.test import TestCase

class ValidationTestCase(TestCase):

    def test_validate_tags(self):
        """
           Simple test for validating tags
        """

        result = validate_tags("komedia, dramat, ")
        self.assertEquals(result, True)

        result = validate_tags("dupa, dupa, dupa")
        self.assertEquals(result, True)

        result = validate_tags("dupa, dupa dupa, dupa")
        self.assertEquals(result, True)

        result = validate_tags("dupa, dupa-dupa, dupa")
        self.assertEquals(result, True)

        result = validate_tags("dupa\", dupa, dupa")
        self.assertEquals(result, False)

        result = validate_tags(u"ąęłżźńćśó, córka, dupa, dupa")
        self.assertEquals(result, True)

        result = validate_tags(u"drop table core_object, dupa, dupa")
        self.assertEquals(result, False)
