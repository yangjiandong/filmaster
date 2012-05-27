from api.tests.utils import ApiTestCase
from django.utils import simplejson as json
from django.conf import settings

import logging
logger = logging.getLogger(__name__)

FILM_KEYS = ('characters_uri', 'description', 'directors', 'image', 'permalink', 
             'production_country_list', 'release_date', 'release_year', 'posts_uri',
             'resource_uri', 'short_reviews_uri', 'title', 'title_localized',
             'tags', 'related_uri', 'links', 'links_uri')

PERSON_KEYS = ('films_directed_uri', 'films_played_uri', 'image', 'name', 
               'permalink', 'resource_uri', 'surname', 'posts_uri')

class GeneralTest(ApiTestCase):

    def test_json(self):
        response = self.client.get(self.API_BASE + "/user/test/", HTTP_HOST='api.' + settings.DOMAIN)
        self.assertEquals(response.status_code, 200)
        # default response should be json
        self.assertEquals(response['Content-Type'], "application/json; charset=utf-8")

    def _test_xml(self):
        response = self.client.get(self.API_BASE + "/user/test/?format=xml", HTTP_HOST='api.' + settings.DOMAIN)
        self.assertEquals(response.status_code, 200)
        logger.info(response['Content-Type'])
        self.assertEquals(response['Content-Type'], "text/xml; charset=utf-8")

    def test_film(self):
        status, film = self.get('/film/pulp-fiction/?include=links')
        self.assertEquals(status, 200)
        self.assertKeys(film, FILM_KEYS)
        self.assertTrue(isinstance(film['directors'], list))
        self.assertPaginatedCollection(self.get(film['characters_uri'])[1])
    
    def test_person(self):
        status, person = self.get('/person/john-travolta/')
        self.assertEquals(status, 200)
        self.assertKeys(person, PERSON_KEYS)
        self.assertPaginatedCollection(self.get(person['films_played_uri'])[1])
        self.assertPaginatedCollection(self.get(person['films_directed_uri'])[1])

