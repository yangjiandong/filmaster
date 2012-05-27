import oauth
import urllib2
import logging
import cgi
logger = logging.getLogger(__name__)

class OAuthHandler(urllib2.BaseHandler):
    def __init__(self, consumer, access_token):
        self.consumer = consumer
        self.access_token = access_token

    def http_request(self, request):
        params = {}
        url = request.get_full_url()
        data = request.get_data()
        logger.debug("request url: %s", url)
        if '?' in url:
          qs = url.split('?',1)[1]
          params.update(dict((k,v[0]) for k,v in cgi.parse_qs(qs).items()))
        if data:
          params.update(dict((k,v[0]) for k,v in cgi.parse_qs(data).items()))

        oauth_request = oauth.OAuthRequest.from_consumer_and_token(
             self.consumer,
             token = self.access_token,
             http_method = request.get_method().upper(),
             http_url = url,
             parameters = params)
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, token = self.access_token)
        oauth_headers = oauth_request.to_header()
        request.headers.update(oauth_headers)
        return request

    def http_response(self, request, response):
        return response

    https_request = http_request
    https_response = http_response

def oauth_opener(consumer, access_token):
  return urllib2.build_opener(OAuthHandler(consumer, access_token))
