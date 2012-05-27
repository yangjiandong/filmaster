from api.tests.utils import ApiTestCase
from django.utils import simplejson as json

import logging
logger = logging.getLogger(__name__)

SHORT_REVIEW_KEYS = (
    "resource_uri", "film_uri", "created_at", "updated_at", "review_text",
    "comments_uri",
)

class ShortReviewTest(ApiTestCase):
  
    def test_short_review(self):
        status, data = self.get("/user/test/short-reviews/")
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        
        review = dict(
           review_text = 'x',
        )
        status, data = self.put('/user/test/short-reviews/pulp-fiction/', review, 'test')
        self.assertEquals(status, 400)

        review = dict(
           review_text = 'lorem ipsum ...'*100,
        )
        status, data = self.put('/user/test/short-reviews/pulp-fiction/', review, 'test')
        self.assertEquals(status, 400)

        review = dict(
           review_text = 'lorem ipsum ...',
        )
        status, data = self.put('/user/test/short-reviews/pulp-fiction/', review, 'test')
        self.assertEquals(status, 200)
        self.assertEquals(data['review_text'], 'lorem ipsum ...')
        self.assertKeys(data, SHORT_REVIEW_KEYS)

        status, data = self.get('/user/test/activities/short_reviews/')
        self.assertTrue(len(data['objects'])>0)

        status, data = self.get('/planet/?shorts')
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertTrue(len(data['objects'])>0)


        status, data = self.delete('/user/test/short-reviews/pulp-fiction/', 'test')
        self.assertEquals(status, 200)

        status, data = self.delete('/user/test/short-reviews/pulp-fiction/', 'test')
        self.assertEquals(status, 404)
        