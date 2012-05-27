import urllib, urllib2
import json

class API(object):
    def __init__(self, access_token=None):
        self.access_token = access_token

    BASE_URL = 'https://graph.facebook.com'

    def get_params(self, **kw):
        params = {}
        if self.access_token:
            params['access_token'] = self.access_token
        params.update(kw)
        return params

    def get(self, path, **kw):
        if not path.startswith('http:') and not path.startswith('https:'):
            params = self.get_params(**kw)
            url = '%s%s?%s' % (self.BASE_URL, path, urllib.urlencode(params))
        else:
            url = path
        return json.loads(urllib2.urlopen(url).read())

    def post(self, path, **kw):
        params = self.get_params(**kw)
        url = self.BASE_URL + path
        data = urllib.urlencode(params)
        return json.loads(urllib2.urlopen(url, data).read())

    def delete(self, path, **kw):
        params = self.get_params(**kw)
        url = self.BASE_URL + path
        request = urllib2.Request(url, data=urllib.urlencode(params))
        request.get_method = lambda:'DELETE'
        return json.loads(urllib2.urlopen(request).read())
