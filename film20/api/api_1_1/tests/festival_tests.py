from api.tests.utils import ApiTestCase
from django.utils import simplejson as json
from django.contrib.auth.models import User

import logging
logger = logging.getLogger(__name__)

from blog.models import Post

class FestivalTest(ApiTestCase):
  
    def _test_festival(self):
        status, data = self.get("/film/pulp-fiction/")
        logger.info(data)
        status, data = self.get("/country/PL/festival/")
        self.assertEquals(status, 200)
        self.assertPaginatedCollection(data)
        len_pl = len(data['objects'])
        self.assertTrue(len_pl)

        status, data = self.get("/country/DE/festival/")
        self.assertTrue(len(data['objects']))

        user = User.objects.get(username='test')

        # move user to Warsaw
        profile = user.get_profile()
        profile.latitude, profile.longitude = ("52.2", "21")
        profile.save()
        
        status, data = self.get("/country/PL/festival/?distance=30", 'test')
        
        self.assertTrue(len(data['objects']) < len_pl)
        
                
