from api.tests.utils import ApiTestCase
from django.utils import simplejson as json

import logging
logger = logging.getLogger(__name__)

class RatingsTest(ApiTestCase):
  
    def test_ratings(self):
        # non-existent user or film should return 404
      
        status, data = self.get("/user/test/ratings/film/pulp-fiction/")
        self.assertEquals(status, 200)
        self.assertEquals(data['objects'], [])

        # try create not own rating 
        status, data = self.put("/user/alice/ratings/film/pulp-fiction/1/", {'rating':1}, 'test')
        self.assertEquals(status, 401)
        
        # create rating
        status, data = self.put("/user/test/ratings/film/pulp-fiction/1/", {'rating':1}, 'test')
        self.assertEquals(status, 200)

        status, data = self.get("/user/test/ratings/film/pulp-fiction/")
        self.assertEquals(status, 200)
        self.assertEquals(data['objects'][0]['rating'], 1)
        self.assertEquals(data['objects'][0]['type'], 1)

        # update rating
        status, data = self.put("/user/test/ratings/film/pulp-fiction/1/", {'rating':2}, 'test')
        self.assertEquals(status, 200)

        # invalud ratings
        for r in (0, 11, ''):
            status, data = self.put("/user/test/ratings/film/pulp-fiction/1/", {'rating':r}, 'test')
            self.assertEquals(status, 400)

        status, data = self.get("/user/test/ratings/film/pulp-fiction/")
        self.assertEquals(status, 200)
        self.assertEquals(data['objects'][0]['rating'], 2)
        self.assertEquals(data['objects'][0]['type'], 1)

        
        status, data = self.get('/user/test/films-unrated/')
        self.assertEquals(status, 200)
        self.assertTrue(data['objects'])
        
        self.assertFalse(any(f['permalink']=='pulp_fiction' for f in data['objects']))
        
        # try to cancel not own rating
        status, data = self.delete("/user/alice/ratings/film/pulp-fiction/1/", 'test')
        self.assertEquals(status, 401)

        # try to set invalid rate type
        status, data = self.delete("/user/alice/ratings/film/pulp-fiction/99/", 'test')
        self.assertEquals(status, 401)

        # cancel rating
        status, data = self.delete("/user/test/ratings/film/pulp-fiction/1/", 'test')
        self.assertEquals(status, 200)

        status, data = self.get("/user/test/ratings/film/pulp-fiction/")
        self.assertEquals(status, 200)
        self.assertEquals(data['objects'], [])

