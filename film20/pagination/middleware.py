from django.utils.translation import ugettext as _
import logging
logger = logging.getLogger(__name__)
import django.core.context_processors

def get_page(self):
    """
    A function which will be monkeypatched onto the request to get the current
    integer representing the current page.
    """
    try:
        return int(self.REQUEST[_('page')])
    except (KeyError, ValueError, TypeError):
        return 1

def create_cache_key(self):
                                               
    return self.build_absolute_uri() + self.user

class PaginationMiddleware(object):
    """
    Inserts a variable representing the current page onto the request object if
    it exists in either **GET** or **POST** portions of the request.
    """
    def process_request(self, request):
        request.__class__.page = property(get_page)
        #request.__class__.cache_key = request.build_absolute_uri() + str(request.user)