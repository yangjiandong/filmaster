from film20.utils.test import TestCase, Client 
from piston.models import Consumer, Token
from django.contrib.auth.models import User
from django.conf import settings
import oauth
import re
import cgi
from django.utils import simplejson as json
import logging
logger = logging.getLogger(__name__)

class OAuthClient(Client):
    def __init__(self, consumer, access_token):
        super(OAuthClient, self).__init__()
        self.consumer = consumer
        self.access_token = access_token

    def request(self, **request):
        params = {}
        qs = request.get('QUERY_STRING')
        params.update(dict((k,v[0]) for k,v in cgi.parse_qs(qs).items()))

        url = 'http://api.' + settings.DOMAIN + request.get('PATH_INFO') + ('?' + qs if qs else '')
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
            self.consumer,
            token = self.access_token,
            http_method = request.get('REQUEST_METHOD'),
            http_url = url,
            parameters = params)
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, token = self.access_token)
        oauth_headers = oauth_request.to_header()
        request.update(('HTTP_%s'%key.upper(), value) for (key,value) in oauth_headers.items())
        return super(OAuthClient, self).request(**request)

class ApiTestCase(TestCase):
    fixtures = ['test_users.json', 'test_app.json', 'test_films.json']
    def __init__(self, *args, **kw):
        TestCase.__init__(self, *args, **kw)
        self.VER = re.search('api.api_([0-9_]+).*', self.__class__.__module__).group(1).replace('_', '.')
        self.API_BASE = "/" + self.VER
      
    def setUp(self):
        from django.core.cache import cache
        try:
            from django.core.cache.backends.locmem import LocMemCache

            if isinstance(cache, LocMemCache): 
                cache.clear()
                logger.info("cache cleared")
        except ImportError, e:
            logger.warning(e)
                        
        self.consumer = Consumer.objects.get(name='test')
        self.user = User.objects.get(username='test')
        self.access_token = Token.objects.filter(consumer = self.consumer, user=self.user, token_type=Token.ACCESS)[0]
        self.auth_client = OAuthClient(self.consumer, self.access_token)
    
    def authorized_client(self, username):
        user = User.objects.get(username=username)
        access_token = Token.objects.filter(consumer = self.consumer, user=user, token_type=Token.ACCESS)[0]
        return OAuthClient(self.consumer, access_token)
    
    def _response(self, response):
        try:
            data = json.loads(response.content)
        except:
            data = None
        if response.status_code == 500:
            logger.error(response.content)
        else:
            logger.debug("response: %r", data)
        return response.status_code, data

    def get(self, path, username=None):
        path = self._normalize_path(path)
        client = username and self.authorized_client(username) or self.client
        return self._response(client.get(path))

    def put(self, path, data, username=None, content_type='application/json', method='put'):
        path = self._normalize_path(path)
        client = username and self.authorized_client(username) or self.client
        if content_type.startswith('application/json'):
            if isinstance(data, (dict, list, tuple)):
                # TODO - very dirty HACK
                # client.put tries to call http.urlencode on data and fails when data is json string
                # http.urlencode calls items method od data when avaliable, so:
                class _data(str): 
                    def items(self): return ('json', self),
                data = _data(json.dumps(data))
        meth = getattr(client, method)
        return self._response(meth(path, data=data, content_type=content_type))

    def post(self, *args, **kw):
        return self.put(method='post', *args, **kw)

    def delete(self, path, username=None):
        path = self._normalize_path(path)
        client = username and self.authorized_client(username) or self.client
        return self._response(client.delete(path))

    def assertKeys(self, data, keys):
        v = set(data.keys()).issuperset(keys)
        if not v:
            logger.error("missing keys: %r", set(keys) - set(data.keys()))
        self.assertTrue(v)

    def assertValidPaginator(self, paginator):
        self.assertTrue(isinstance(paginator, dict))
        self.assertTrue('next_uri' in paginator)
        self.assertTrue('page' in paginator)
    
    def assertCollection(self, data):
        self.assertTrue(isinstance(data, dict))
        self.assertTrue('objects' in data)
        self.assertTrue(isinstance(data['objects'], list))

    def assertPaginatedCollection(self, data):
        self.assertCollection(data)
        self.assertValidPaginator(data.get('paginator'))

    # we allow for /api/ver/ prefix skipping
    def _normalize_path(self, path):
        if not path.startswith(self.API_BASE):
            path = self.API_BASE + path
        return 'http://api.' + settings.DOMAIN + path
        
