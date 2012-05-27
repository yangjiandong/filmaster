API_PAGE_SIZE = 10

def int_param(request, name, default):
    try:
        return int(request.GET.get(name, default))
    except ValueError, e:
        return default

def paginated_collection(request, object_list, wrap_func=lambda x:x, default_limit=API_PAGE_SIZE):
    from film20.pagination.paginator import InfinitePaginator, EmptyPage
    limit = int_param(request, 'limit', default_limit)
    page_nr = int_param(request, 'page', 1)

    try:
        paginator = InfinitePaginator(object_list, limit)
        page = paginator.page(page_nr)
    except EmptyPage, e:
        from django.http import Http404
        raise Http404
    
    from urllib import urlencode
    
    if page.has_next():
        next_params = request.GET.copy()
        next_params['page'] = page_nr + 1
        next_uri = "%s?%s" % (request.META['PATH_INFO'], urlencode(next_params.items()))
    else:
        next_uri = None

    if page_nr>1:
        prev_params = request.GET.copy()
        prev_params['page'] = page_nr - 1
        prev_uri = "%s?%s" % (request.META['PATH_INFO'], urlencode(prev_params.items()))
    else:
        prev_uri = None
        
    return {
        'objects':list(wrap_func(i) for i in page.object_list)[0:limit], # TODO - quick hack, fix InfinitePaginator
        'paginator': {
            'page': page_nr,
            'next_uri': next_uri,
            'prev_uri': prev_uri,
        }
    }

def collection(request, object_list, wrap_func = lambda x:x):
    return {
        'objects':list(wrap_func(i) for i in object_list),
    }

# function / method debug decorator
def debug_call(func):
    import logging
    logger = logging.getLogger(__name__)
    def wrapper(*args, **kw):
        try:
            logger.debug("%r: args: %r, kw: %r", func, args, kw)
            ret = func(*args, **kw)
            logger.debug("%r: ret: %r", func, ret)    
        except Exception, e:
            logging.exception(e)
            raise
        return ret
    return wrapper

def form_errors(form):
    if form.errors:
        return dict((k, list(unicode(i) for i in v)) for k, v in form.errors.items())
    return {}

def get_list(dict, key):
    if hasattr(dict, 'getlist'):
        # QueryDict case
        return dict.getlist(key)
    value = dict.get(key)
    if value is None: return []
    if not isinstance(value, (list, tuple)):
        value = [value]
    return value

import threading
_thread_local = threading.local()

def get_request():
    return getattr(_thread_local, 'request', None)

def set_request(request):
    _thread_local.request = request

from piston.emitters import Emitter, DateTimeAwareJSONEncoder
from piston.validate_jsonp import is_valid_jsonp_callback_value
from django.utils import simplejson
class JSONEmitter(Emitter):
    """
    JSON emitter, understands timestamps.
    """
    def render(self, request):
        cb = request.GET.get('callback', None)
        try:
            indent = int(request.GET.get('indent',2))
        except:
            indent = None
        
        seria = simplejson.dumps(self.construct(), cls=DateTimeAwareJSONEncoder, ensure_ascii=False, indent=indent)

        # Callback
        if cb and is_valid_jsonp_callback_value(cb):
            return '%s(%s)' % (cb, seria)

        return seria

Emitter.register('json', JSONEmitter, 'application/json; charset=utf-8')

from django.utils.html import strip_tags
from film20.utils.html import unescape
def strip_html(text):
    request = get_request()
    if request and 'striphtml' in request.GET:
        return unescape(strip_tags(text or ''))
    return text

from django.conf import settings
from film20.core.models import Person
from film20.config import urls
from film20.utils.posters import thumbnail_path

def get_hires_image(obj, size=('180', 'auto')):
    if obj.hires_image:
        return u"%s%s" % (settings.MEDIA_URL, thumbnail_path(obj.hires_image, size))
    if isinstance(obj, Person):
        return urls.urls.get('DEFAULT_ACTOR')
    else:
        return urls.urls.get('DEFAULT_POSTER')

