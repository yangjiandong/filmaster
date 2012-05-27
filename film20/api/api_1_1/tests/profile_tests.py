from api.tests.utils import ApiTestCase
from django.utils import simplejson as json

import logging
logger = logging.getLogger(__name__)

USER_KEYS = (
    'username', 'first_name', 'last_name', 'filmbasket_uri',
    'shitlist_uri', 'wishlist_uri', 'ratings_uri', 'films_owned_uri',
    'avatar', 'recommendations_uri', 'date_joined', 'last_login',
    'films_unrated_uri', 'website', 'description', 'gender'
)

class ProfileTests(ApiTestCase):
    
    def test_profile_anonymous(self):
        status, data = self.get("/profile/")
        self.assertEquals(status, 401)

        status, data = self.get("/user/test/")
        self.assertEquals(status, 200)
        self.assertKeys(data, USER_KEYS)

        status, data = self.get("/user/invalid/")
        self.assertEquals(status, 404)

    def test_profile_authorized(self):
        status, data = self.get(self.API_BASE + "/profile/", username='bob')
        self.assertEquals(status, 200)
        self.assertKeys(data, USER_KEYS)
        
        st, data = self.put('/profile/', {'description':'<b>text with</b> tags &amp; entities'}, 'bob')
        self.assertEquals(st, 200)
        
        st, data = self.get('/profile/?striphtml', 'bob')
        self.assertEquals(st, 200)
        self.assertEquals(data['description'], "text with tags & entities")
