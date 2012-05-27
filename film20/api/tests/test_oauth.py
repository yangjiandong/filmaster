from film20.utils.test import TestCase
from django.test import Client
from piston.models import Consumer
import oauth
from django.conf import settings

from film20.core.models import User
import urlparse, cgi

CALLBACK_URL = None
REQUEST_TOKEN_URL = 'http://testserver/oauth/request/token/'
ACCESS_TOKEN_URL = 'http://testserver/oauth/access/token/'

AUTHORIZE_URL = 'http://testserver/oauth/authorize/'
AUTHORIZE_ANON_URL = 'http://testserver/oauth/authorize/anon/'
RESOURCE_URL = 'http://testserver/api/1.1/profile/'

def cgi_headers(oauth_request):
    headers = oauth_request.to_header()
    return dict(('HTTP_%s'%key.upper(), value) for (key,value) in headers.items())

class OAuthTest(TestCase):
    fixtures = ['test_app.json', 'test_users.json']

    def test_oauth_create_tmp_user(self):
        consumer = Consumer.objects.get(name='test')
        
        signature_method_plaintext = oauth.OAuthSignatureMethod_PLAINTEXT()
        signature_method_hmac_sha1 = oauth.OAuthSignatureMethod_HMAC_SHA1()

        client = Client()
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, callback=CALLBACK_URL, http_url=REQUEST_TOKEN_URL)
        oauth_request.sign_request(signature_method_hmac_sha1, consumer, None)
        reply = client.get(REQUEST_TOKEN_URL, **cgi_headers(oauth_request))
        token = oauth.OAuthToken.from_string(reply.content)

        TMP_USERNAME = 'tst-12345678901234567890123456'

        parameters = {'username': TMP_USERNAME, 'password': '1'*30}
        oauth_request = oauth.OAuthRequest.from_token_and_callback(token=token, callback=CALLBACK_URL, http_url=AUTHORIZE_ANON_URL, parameters=parameters)
        oauth_request.sign_request(signature_method_hmac_sha1, consumer, None)
        client = Client()
        reply = client.get(oauth_request.to_url(), **cgi_headers(oauth_request))
        
        tmp_user = User.objects.get(username=TMP_USERNAME, is_active=False)
        self.assertTrue(tmp_user)

        params = cgi.parse_qs(reply.content, keep_blank_values=False)
        verifier = params['oauth_verifier'][0]

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, verifier=verifier, http_url=ACCESS_TOKEN_URL)
        oauth_request.sign_request(signature_method_hmac_sha1, consumer, token)
        reply = client.get(ACCESS_TOKEN_URL, **cgi_headers(oauth_request))
        token = oauth.OAuthToken.from_string(reply.content)

        url = 'http://testserver/api/1.1/profile/register/email/'
        parameters = {'email': 'some@email.pl'}
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_method='POST', http_url=url)
        oauth_request.sign_request(signature_method_hmac_sha1, consumer, token)
        reply = client.post(url, parameters, **cgi_headers(oauth_request))
        print reply
        self.assertEquals(reply.status_code, 200)

        #url = 'http://testserver/api/1.1/profile/register/fb/'
        #parameters = {'access_token': 'fb_access_token'}
        #oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_method='POST', http_url=url)
        #oauth_request.sign_request(signature_method_hmac_sha1, consumer, token)
        #reply = client.post(url, parameters, **cgi_headers(oauth_request))
        #print reply
        #self.assertEquals(reply.status_code, 200)
        #return 

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_method='GET', http_url=RESOURCE_URL)
        oauth_request.sign_request(signature_method_hmac_sha1, consumer, token)
        reply = client.get(RESOURCE_URL, **cgi_headers(oauth_request))
        self.assertEquals(reply.status_code, 200)

        # register normal user based on temporary user
        
        client = Client()
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, callback=CALLBACK_URL, http_url=REQUEST_TOKEN_URL)
        oauth_request.sign_request(signature_method_hmac_sha1, consumer, None)
        reply = client.get(REQUEST_TOKEN_URL, **cgi_headers(oauth_request))
        token = oauth.OAuthToken.from_string(reply.content)

        parameters = {'tmp_user':'tst-12345678901234567890123456'}
        oauth_request = oauth.OAuthRequest.from_token_and_callback(token=token, callback=CALLBACK_URL, http_url=AUTHORIZE_URL, parameters=parameters)
        oauth_request.sign_request(signature_method_hmac_sha1, consumer, None)
        client = Client()
        reply = client.get(oauth_request.to_url(), **cgi_headers(oauth_request))
        reg_url = reply['Location']

        reply = client.post(reg_url, {'email': 'testowy@test.pl', 'username':'testowy', 'password1':'123', 'password2':'123'})

        self.assertTrue(User.objects.get(username='testowy', is_active=True).id == tmp_user.id)

    def _test_login(self):
        u = User.objects.get(username='test')
        u.set_password('test')
        u.save()

        c = Client()
        print c.post('/konto/login/', {'username': 'test', 'password': 'test'})

        print c.get('/')

