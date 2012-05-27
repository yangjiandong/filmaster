from api.tests.utils import ApiTestCase
from django.utils import simplejson as json

import logging
logger = logging.getLogger(__name__)

class BasketTest(ApiTestCase):
  
    def test_basket(self):
        # non-existent user or film should return 404

        status, data = self.get("/user/test/filmbasket/")
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertEquals(data['objects'], [])

        status, data = self.get("/user/test/films-owned/")
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertEquals(data['objects'], [])

        status, data = self.get("/user/test/wishlist/")
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertEquals(data['objects'], [])

        status, data = self.get("/user/test/shitlist/")
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertEquals(data['objects'], [])

        item = dict(
            wishlist=1,
            owned=1,
        )
        item2 = dict(
            wishlist=9,
        )
        # pulpfiction to wishlist and films-owned
        status, data = self.put('/user/test/filmbasket/pulp-fiction/', item, 'test')
        self.assertEquals(status, 200)

        # godfather to shitlist (sorry, just testing ;)
        status, data = self.put('/user/test/filmbasket/the-godfather/', item2, 'test')
        self.assertEquals(status, 200)

        _, data = self.get('/user/test/wishlist/?include=film')
        self.assertEquals(data['objects'][0]['film']['permalink'], 'pulp-fiction')

        _, data = self.get('/user/test/films-owned/?include=film')
        self.assertEquals(data['objects'][0]['film']['permalink'], 'pulp-fiction')

        _, data = self.get('/user/test/shitlist/?include=film')
        self.assertEquals(data['objects'][0]['film']['permalink'], 'the-godfather')

        godfather = data['objects'][0]

        status, _ = self.put((godfather['resource_uri']), {'wishlist':1}, 'test')
        self.assertEquals(status, 200)

        _, data = self.get('/user/test/wishlist/')
        self.assertEquals(len(data['objects']), 2)

        _, data = self.get('/user/test/shitlist/')
        self.assertEquals(len(data['objects']), 0)

        _, data = self.get('/film/pulp-fiction/?include=auth_basket')
        self.assertFalse(data['auth_basket'])

        _, data = self.get('/film/pulp-fiction/?include=auth_basket', 'test')
        self.assertTrue(data['auth_basket'])

        _, data = self.get('/user/test/filmbasket/pulp-fiction/?include=film,film.basket')
        self.assertTrue(data['film']['basket'])

        _, data = self.get('/user/test/filmbasket/pulp-fiction/?include=film')
        self.assertFalse('basket' in data['film'])

        
        status, data = self.delete((godfather['resource_uri']), 'test')
        self.assertEquals(status, 200)

        status, data = self.delete((data['resource_uri']), 'test')
        self.assertEquals(status, 404)
