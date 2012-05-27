from api.tests.utils import ApiTestCase
from django.utils import simplejson as json

import logging
logger = logging.getLogger(__name__)

WALLPOST_KEYS = (
    "resource_uri", "created_at", "updated_at", "review_text", "comments_uri",
)

class ShortReviewTest(ApiTestCase):
  
    def test_wallpost(self):
        status, data = self.get("/user/test/wall-posts/")
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        
        review = dict(
           review_text = '',
        )
        status, data = self.post('/user/test/wall-posts/', review, 'test')
        self.assertEquals(status, 400)

        review = dict(
           review_text = 'lorem ipsum ...'*100,
        )
        status, data = self.post('/user/test/wall-posts/', review, 'test')
        self.assertEquals(status, 400)

        review = dict(
           review_text = 'lorem ipsum ...',
        )
        status, data = self.post('/user/test/wall-posts/', review, 'test')
        self.assertEquals(status, 200)
        self.assertEquals(data['review_text'], 'lorem ipsum ...')
        self.assertKeys(data, WALLPOST_KEYS)

        # test updates
        status, data = self.put(data['resource_uri'], review, 'test')
        self.assertEquals(status, 200)
        
        review['review_text'] = 'lorem ipsum ...' * 100
        status, data = self.put(data['resource_uri'], review, 'test')
        self.assertEquals(status, 400)

        status, data = self.get('/user/test/wall-posts/')
        self.assertTrue(len(data['objects'])>0)

 
