import cgi
import urllib

import logging
logger = logging.getLogger(__name__)

from django.utils.safestring import mark_safe
from django import template
from django.utils.translation import ugettext, ugettext_noop

register = template.Library()

class FilterLinkNode(template.Node):
    def __init__(self, bits, node_list):
        self.bits = bits
        self.node_list = node_list

    def render(self, context):
        bits = [b.resolve(context) for b in self.bits]
        qs = bits[0]
        default = "default" in bits[1:]
        request = context['request']

        if '#' in qs:
            qs, fragment = qs.split('#', 1)
            fragment = '#' + fragment
        else:
            fragment = ""

        qs = cgi.parse_qsl(qs)
        params = dict(request.GET.items())
        page_key = ugettext('page')

        if page_key in params:
            del params[page_key]

        params.update(qs)

        if not all(k in request.GET for (k,v) in qs):
            selected = default
        else:
            selected = all(request.GET.get(k)==v for (k,v) in qs)

        html = """<a href="?%(qs)s" class="%(class)s">""" % {
            'qs':urllib.urlencode(params) + fragment,
            'class':selected and "selected" or "",
        }

        out = [html]
        out.append(self.node_list.render(context))
        out.append('</a>')
        return ''.join(out)


@register.tag
def filterlink(parser, token):
    bits = token.split_contents()[1:]
    bits = [parser.compile_filter(b) for b in bits]
    nodelist = parser.parse(('endfilterlink',))
    parser.delete_first_token()
    return FilterLinkNode(bits, nodelist)
