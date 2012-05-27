from api.tests.utils import ApiTestCase
from django.utils import simplejson as json, unittest
from django.conf import settings

import logging
logger = logging.getLogger(__name__)

class SearchTest(ApiTestCase):

    @unittest.skipIf(not settings.SOLR_TESTS, "solr tests are disabled")
    def test_search(self):
        status, result = self.get("/search/?phrase=pulp")
        self.assertEquals(status, 200)
        for key in ('films', 'persons', 'users'):
            self.assertTrue(key in result)
            self.assertTrue('best_results' in result[key])
            self.assertTrue('results' in result[key])

        status, result = self.get("/search/film/?phrase=pulp")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results'] and 'results' in result)

        status, result = self.get("/search/person/?phrase=travolta")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results'] and 'results' in result)

        status, result = self.get("/search/user/?phrase=test")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results'] and 'results' in result)

        status, result = self.get("/search/film/?phrase=vaiWoc5Dai")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results']==[] and result['results']==[])

        status, result = self.get("/search/person/?phrase=vaiWoc5Dai")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results']==[] and result['results']==[])

        status, result = self.get("/search/user/?phrase=vaiWoc5Dai")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results']==[] and result['results']==[])

        status, result = self.get("/search/film/?phrase=")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results']==[] and result['results']==[])

        status, result = self.get("/search/person/?phrase=")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results']==[] and result['results']==[])

        status, result = self.get("/search/user/?phrase=")
        self.assertEquals(status, 200)
        self.assertTrue(result['best_results']==[] and result['results']==[])

