from api.tests.utils import ApiTestCase
from django.utils import simplejson as json
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

COMMENT_KEYS = ('comment', 'resource_uri', 'parent_uri', 'date_modified', 'date_submitted')

from blog.models import Post

class CommentsTest(ApiTestCase):

    def comment_object(self, obj):

        logger.info(obj)
        comments_uri = obj['comments_uri']
        
        status, data = self.get(comments_uri)
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertEquals(data['objects'], [])
        
        comment = dict(
            comment = 'comment 123',
            object_uri = obj['resource_uri']
        )

        too_short_comment = dict(
            comment = '123',
            object_uri = obj['resource_uri']
        )

        no_obj_comment = dict(
            comment = 'comment 123',
        )

        # anonymous try:
        status, data = self.post('/comment/', comment)
        self.assertEquals(status, 401)

        status, data = self.post('/comment/', {}, 'test')
        self.assertEquals(status, 400)

        if getattr(settings, "MIN_CHARACTERS_COMMENT_APPLY", True):
            # too short
            status, data = self.post('/comment/', too_short_comment, 'test')
            self.assertEquals(status, 400)
            self.assertTrue('comment' in data)

        status, _ = self.post('/comment/', no_obj_comment, 'test')
        self.assertEquals(status, 400)

        status, data = self.post('/comment/', comment, 'test')
        self.assertEquals(status, 200)
        self.assertKeys(data, COMMENT_KEYS)

        # dupe
        status, _ = self.post('/comment/', comment, 'test')
        self.assertEquals(status, 400)

        sub_comment = dict(
            comment='sub comment',
            object_uri=obj['resource_uri'],
            parent_uri=data['resource_uri'],
        )
        
        status, data = self.post('/comment/', sub_comment, 'test')
        self.assertEquals(status, 200)
        self.assertEquals(data['parent_uri'], sub_comment['parent_uri'])
        
        status, data = self.get(comments_uri)
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 2)

        status, data = self.get('/user/test/activities/comments/')
        self.assertTrue(len(data['objects'])>0)

        status, data = self.get('/planet/?comments')
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertTrue(len(data['objects'])>0)
        
    def test_post_comment(self):
        post = dict(
           title = 'post title',
           body = 'post body',
        )
        status, data = self.post('/user/test/posts/', post, 'test')
        self.assertEquals(status, 200)

        logger.info('commenting object %r', data)
        self.comment_object(data)
        

    def test_short_review_comment(self):
        short = dict(
           review_text = 'short review text'
        )
        status, data = self.put('/user/test/short-reviews/pulp-fiction/', short, 'test')
        self.assertEquals(status, 200)

        self.comment_object(data)

