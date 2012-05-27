from api.tests.utils import ApiTestCase
from django.utils import simplejson as json
import logging
logger = logging.getLogger(__name__)

FOLLOWING_KEYS = ('user_uri', 'resource_uri')

class FollowersTest(ApiTestCase):
  
    def test_followers(self):
        status, data = self.get("/user/test/following/")
        self.assertPaginatedCollection(data)
        self.assertFalse(data['objects'])

        status, data = self.get("/user/test/followers/")
        self.assertPaginatedCollection(data)
        self.assertFalse(data['objects'])

        status, data = self.get("/user/test/friends/")
        self.assertPaginatedCollection(data)
        self.assertFalse(data['objects'])
        
        status, data = self.put("/profile/following/alice/", {}, 'test')
        self.assertEquals(status, 200)

        status, data = self.get("/user/test/following/")
        self.assertPaginatedCollection(data)
        self.assertTrue(data['objects'][0]['user_uri'] == '/1.0/user/alice/')

        status, data = self.get("/user/alice/followers/")
        self.assertPaginatedCollection(data)
        self.assertTrue(data['objects'][0]['user_uri'] == '/1.0/user/test/')

        status, data = self.get("/user/test/friends/")
        self.assertPaginatedCollection(data)
        self.assertFalse(data['objects'])
        
        status, data = self.put("/profile/following/test/", {}, 'alice')
        self.assertEquals(status, 200)
        
        status, data = self.get("/user/alice/following/")
        self.assertEquals(len(data['objects']), 1)

        status, data = self.get("/user/test/friends/")
        self.assertPaginatedCollection(data)
        self.assertEquals(len(data['objects']), 1)

        status, data = self.post("/profile/following/", {'user_uri':'/1.0/user/bob/'}, 'test')
        self.assertEquals(status, 200)
        self.assertEquals(data['user_uri'], '/1.0/user/bob/')

        status, data = self.post("/profile/following/", {'user_uri':'/1.0/user/test/'}, 'test')
        self.assertEquals(status, 400)
