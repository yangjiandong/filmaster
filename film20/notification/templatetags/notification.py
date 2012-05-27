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

from django import template
from django.utils import simplejson
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.utils.encoding import smart_unicode

from hashlib import md5
import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.filter
def json(value):
    return mark_safe(simplejson.dumps(value))

@register.filter
def jsonstr(value):
    return mark_safe(simplejson.dumps(smart_unicode(value)))

@register.filter
def truncate(value, n):
    value = smart_unicode(value)
    n = int(n)
    if len(value) > n:
        value = value[0:n-3] + u"..."
    return value

def short_url(value):
    from urllib2 import urlopen
    from urllib import urlencode
    
    value = smart_unicode(value)
    key = "short_url_%s" % md5(value).hexdigest()
    short = cache.get(key)
    if short is None:
        params = dict(
            longUrl=value,
            login='mrkits',
            apiKey='R_03ac99e88a054d31f9c80e4b2dc71586',
        )
        response = simplejson.loads(urlopen('http://api.bitly.com/v3/shorten?' + urlencode(params)).read())
        if response and response.get('status_code') == 200:
            short = response['data']['url']
            cache.set(key, short)
        else:
            short = value
    return short
register.filter('short_url', short_url)

import re
URL_RE = re.compile(r"http://[\w.\-,\?/&=#%:]+")

def short_urls(value):
    value = smart_unicode(value)
    for url in set(URL_RE.findall(value)):
        value = value.replace(url, short_url(url))
    return value
register.filter('short_urls', short_urls)

def _cut(value, length, encoder, decoder):
    value = encoder(value)
    n = len(value) - length
    while n>0:
        try:
            v = decoder(value[:n])
            if len(v)>=3:
                v = v[0:-3] + "..."
            return v
        except Exception, e:
            n -= 1
    return u''

def _create_cutter(name, n):
    def _autocut(value, ctx):
        value = smart_unicode(value)
        pass_nr = ctx.get('cut_pass')
        length = ctx.get('cut_len', 0)
        encoder = ctx.get('cut_encoder', lambda s:s.encode('utf-8'))
        decoder = ctx.get('cut_decoder', lambda s:s.decode('utf-8'))
        if n > pass_nr:
            v = value
        elif n == pass_nr:
            v = _cut(value, length, encoder, decoder)
        else:
            v = ''
        return v
    register.filter(name, _autocut)

_create_cutter('autocut', 1)
_create_cutter('autocut1', 1)
_create_cutter('autocut2', 2)
_create_cutter('autocut3', 3)

from django.template.loader import select_template
from django.template import Template

def render_template(template, ctx, max_len=None):
    ctx['ctx'] = ctx
    if not isinstance(template, Template):
        template = select_template(template)
    pass_nr = 0 
    while pass_nr <= 3:
        ctx['cut_pass'] = pass_nr
        out = template.render(ctx).strip()
        if not max_len:
            return out
        encoder = ctx.get('cut_encoder', lambda s:s.encode('utf-8'))
        utf_out = encoder(out)
        cut_len = len(utf_out) - max_len
        if cut_len <=0: break
        ctx['cut_len'] = cut_len
        pass_nr += 1
    if cut_len > 0:
        logger.warning("can't cut template, are you using autocut tags?")
    return out

