from film20.utils.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings

from film20.geo.middleware import GeoMiddleware

class GeoTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def apply_middlewares(self, request):
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.auth.middleware import AuthenticationMiddleware
        SessionMiddleware().process_request(request)
        AuthenticationMiddleware().process_request(request)
        GeoMiddleware().process_request(request)

    def test_geo(self):
        request = self.factory.get('/')

        # no html5 geolocation, no client ip
        self.apply_middlewares(request)

        # no info in request, location from settings
        self.assertEquals(type(request.geo), dict)
        self.assertEquals(request.geo['source'], 'settings')
        self.assertEquals(request.geo['country_code'], settings.COUNTRY_CODE)

        request = self.factory.get('/', 
                HTTP_ACCEPT_LANGUAGE = 'de,en-US;q=0.8,en;q=0.6,en-GB;q=0.4')
        self.apply_middlewares(request)
        self.assertEquals(request.geo['source'], 'accept_language')
        self.assertEquals(request.geo['country_code'], 'DE')
        self.assertEquals(request.geo['timezone'], 'Europe/Berlin')

        request = self.factory.get('/', 
                HTTP_ACCEPT_LANGUAGE = 'en-AU;q=0.8,en;q=0.6,en-GB;q=0.4')
        self.apply_middlewares(request)
        self.assertEquals(request.geo['country_code'], 'AU')
        self.assertEquals(request.geo['timezone'], 'Australia/Sydney')

        request = self.factory.get('/',
                REMOTE_ADDR = '88.198.16.247')
        self.apply_middlewares(request)
        self.assertEquals(request.geo['country_code'], 'DE')
        self.assertEquals(request.geo['timezone'], 'Europe/Berlin')
        self.assertEquals(request.geo['source'], 'geoip')

        request = self.factory.get('/')
        request.COOKIES['geolocation'] = '%7B%22timestamp%22%3A1316343536049%2C%22coords%22%3A%7B%22heading%22%3Anull%2C%22altitude%22%3Anull%2C%22latitude%22%3A52.5%2C%22accuracy%22%3A162%2C%22longitude%22%3A13.5%2C%22speed%22%3Anull%2C%22altitudeAccuracy%22%3Anull%7D%7D' 
        self.apply_middlewares(request)
        self.assertEquals(request.geo['source'], 'html5')
        self.assertEquals(request.geo['country_code'], 'DE')

        self.assertEquals(str(request.timezone), 'Europe/Berlin')

