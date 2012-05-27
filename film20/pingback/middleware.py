from django.core import urlresolvers
from pingback import ping_func
from django_xmlrpc import xmlrpcdispatcher

class PingbackMiddleware(object):
    def __init__(self):
        try:
            self.xmlrpc_url = urlresolvers.reverse('xmlrpc')
        except urlresolvers.NoReverseMatch:
            # this happens upon testing, because contrib.auth tests replace
            # settings.ROOT_URLCONF
            self.xmlrpc_url = None

        # register this method in the dispatcher
        xmlrpcdispatcher.register_function(ping_func, 'pingback.ping')

    def process_response(self, request, response):
        if response.status_code == 200 and self.xmlrpc_url:
            response['X-Pingback'] = request.build_absolute_uri(self.xmlrpc_url)
        return response

