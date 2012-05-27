import logging
logger = logging.getLogger(__name__)

from django.utils import simplejson as json

from api.tests.utils import ApiTestCase
from film20.core.models import Film
from film20.useractivity.models import UserActivity

POST_KEYS = (
    "resource_uri", "comments_uri", "created_at", "updated_at", 
    "title", "body"
)

from blog.models import Post

class PostTest(ApiTestCase):
  
    def test_post(self):
        status, data = self.get("/user/test/posts/")
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        
        post = dict(
           title = 'post title',
        )
        # no body provided
        status, data = self.post('/user/test/posts/', post, 'test')
        self.assertEquals(status, 400)
#        self.assertTrue('body' in data)

        post['body'] = 'post body'

        status, data = self.post('/user/test/posts/', post, 'test')
        self.assertEquals(status, 200)
        self.assertKeys(data, POST_KEYS)
        # new posts are drafts
        self.assertEquals(data['status'], Post.DRAFT_STATUS)
        
        resource_uri = data['resource_uri']
     
        status, data = self.post('/user/test/posts/', post, 'test')
        # test duplicate post
        self.assertEquals(status, 400)

        # edit post
        post = dict(
            title = 'new title',
            body = 'new body',
            status = Post.PUBLIC_STATUS,
        )
        
        status, data = self.put(resource_uri, post, 'test')
        logger.info('post data: %r', data)
        self.assertEquals(status, 200)
        self.assertEquals(data['body'], 'new body')
        self.assertEquals(data['title'], 'new title')
        self.assertEquals(data['status'], Post.PUBLIC_STATUS)

        resource_uri = data['resource_uri']
        related_films = data['related_films_uri']
        related_persons = data['related_persons_uri']
        
        status, data = self.post(related_films, {'film_uri':self.API_BASE+'/film/pulp-fiction/'}, 'test')
        self.assertEquals(status, 200)

        status, data = self.post(related_persons, {'person_uri':self.API_BASE+'/person/john-travolta/'}, 'test')
        self.assertEquals(status, 200)

        status, data = self.get(self.API_BASE + '/film/pulp-fiction/posts/')
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 1)

        status, data = self.get(self.API_BASE + '/person/john-travolta/posts/')
        self.assertEquals(status, 200)
        self.assertEquals(len(data['objects']), 1)

        status, data = self.get(related_films)
        self.assertPaginatedCollection(data)
        self.assertEquals(len(data['objects']), 1)

        status, activities = self.get('/user/test/activities/posts/')
        self.assertTrue(len(activities['objects'])>0)
        
        # change title of published post, permalink (and resource_uri) shouldn't change
        data['title'] = 'another title'
        status, data = self.put(resource_uri, post, 'test')
        self.assertEquals(status, 200)

        status, data = self.get('/planet/?reviews')
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertTrue(len(data['objects'])>0)

        status, data = self.get('/planet/?comments')
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        self.assertTrue(len(data['objects'])==0)
        
        status, data = self.get('/planet/?tags=sometag')
        self.assertFalse(data['objects'])
        
        film = Film.objects.get(permalink='pulp-fiction')
        film.save_tags('sometag')
        
        status, data = self.get('/planet/?tags=sometag')
        self.assertTrue(data['objects'])        

        status, data = self.delete(resource_uri, 'test')
        self.assertEquals(status, 200)
