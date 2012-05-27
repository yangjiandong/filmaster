import cgi
import urllib

import logging
logger = logging.getLogger(__name__)

from django.utils.safestring import mark_safe
from django import template
from django.utils.translation import ugettext, ugettext_noop
from django.utils.encoding import smart_str

register = template.Library()

@register.simple_tag(takes_context=True)
def qs_copy(context, name=None, value=None, name1=None, value1=None):
    request = context['request']

    params = dict(request.GET.items())
    if name and value:
        params[name] = value
    if name1 and value1:
        params[name1] = value1
    
    return mark_safe(urllib.urlencode(params))

@register.simple_tag(takes_context=True)
def qs_selected(context, name, value):
    request = context['request']
    value = smart_str(value)

    params = dict(request.GET.items())
    params[name] = value
    
    logger.info(params)
    
    return request.GET.get(name) == value and "selected" or ""
    
