#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2009 Filmaster (Borys Musielak, Adam Zielinski).
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.functional import Promise 
from django.utils.encoding import force_unicode 
import re

class LazyEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return super(LazyEncoder, self).default(obj)

class JSONResponse(HttpResponse):
    """
    A simple subclass of ``HttpResponse`` which makes serializing to JSON easy.
    """
    def __init__(self, object, is_iterable = True):
        if is_iterable:
            content = serialize('json', object)
        else:
            content = simplejson.dumps(object, cls=LazyEncoder)
        super(JSONResponse, self).__init__(content, mimetype='application/json')

from django.views.decorators.cache import never_cache
def json_response(func):
    @never_cache
    def wrapper(request, *args, **kw):
        return JSONResponse(func(request, *args, **kw), False)
    return wrapper

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

class XMLResponse(HttpResponse):
    """
    A simple subclass of ``HttpResponse`` which makes serializing to XML easy.
    """
    def __init__(self, object, is_iterable = True):
        if is_iterable:
            content = serialize('xml', object)
        else:
            content = object
        super(XMLResponse, self).__init__(content, mimetype='application/xml')

def json_return(context):
    json = simplejson.dumps(context, ensure_ascii=False)
    return HttpResponse(json, mimetype='application/json')
    
def json_success():
    context = {               
        'success': True,
    }
    return json_return(context)

def json_error(reason=None, errors=None):
    print("json_error begin")
    context = {               
        'success': False,
        'reason': reason,        
    }
    if errors:
        context.update({'errors': errors  })
    print("json_error end")
    return json_return(context)

def needle_in_haystack(needle, haystack): 
    reneedle = re.compile(needle)
    return needle in haystack

def proccess_json_response(response):
    """
       Takes json response as string in format {"data": <key>, "success" <key>}
       and return keys
    """
    pattern = r"{\"data\": (\w+), \"success\": (\w+)}"
    a = re.search(pattern, response)
    return a.group(1), a.group(2)

# android US temporary mapped to iphone templates
USER_AGENTS = (
  ('iPhone', 'iphone'),
  ('Android', 'iphone'),
)

# compile regexps
USER_AGENTS = tuple((re.compile(s), name) for (s, name) in USER_AGENTS)

# return tuple of templates with UserAgent-dependent template first (if match found)
def ua_template(request, path):
    ua = request.META.get('HTTP_USER_AGENT', '')
    for r, name in USER_AGENTS:
        if r.search(ua):
            return "%s/%s" % (name, path), path
    return path

def is_mobile(request):
    ua = request.META.get('HTTP_USER_AGENT', '')
    return any(r.search(ua) for (r, name) in USER_AGENTS)

from django.shortcuts import render_to_response
from django.template import RequestContext

def direct_to_template(request, template, extra_context=None, mimetype=None):
    return render_to_response(template, extra_context,
                              context_instance=RequestContext(request),
                              mimetype=mimetype)
    
