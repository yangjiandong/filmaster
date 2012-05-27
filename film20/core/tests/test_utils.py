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
from film20.utils.test import TestCase, is_postgres
from django.utils import unittest

from film20.core.models import Film

class UtilsTestCase(TestCase):
    fixtures = ['test_films.json']
    @unittest.skipIf(not is_postgres, "sqlite is not supported yet")
    def test_raw_query_paging(self):
        all_films = list(Film.objects.all().order_by('id'))
        raw_query = Film.objects.raw("select * from core_film order by parent_id")
        q1 = raw_query[1:5]
        self.assertTrue('offset 1' in q1.raw_query.lower())
        self.assertTrue('limit 4' in q1.raw_query.lower())
        
        q2 = q1[1:100]
        self.assertTrue('offset 2' in q2.raw_query.lower())
        self.assertTrue('limit 3' in q2.raw_query.lower())
        
        self.assertEquals(q2[1], all_films[3])
        self.assertEquals(len(list(q2)), 3)

    def _test_query_cache(self):
        films = Film.objects.cache().filter(permalink='pulp-fiction')
        self.assertEquals(len(films), 1)
        
        f = films[0]
        f.permalink = 'pulp-fiction-broken'
        f.save()

        # will only work if cached
        films = Film.objects.cache().filter(permalink='pulp-fiction')
        self.assertEquals(len(films), 1)
        
        films.invalidate()

        films = Film.objects.cache().filter(permalink='pulp-fiction')
        self.assertEquals(len(films), 0)

    def _test_query_postprocess(self):
        self.executed = False
        def fix(iterator, **kw):
            self.executed = True
            for f in iterator:
                f.postprocessed = True
                yield f
                
        films = Film.objects.all().postprocess(fix)
        
        # test if postprocessing is lazy
        self.assertFalse(self.executed)
        film = films[0]
        self.assertTrue(self.executed)

        self.assertTrue(film.postprocessed)
