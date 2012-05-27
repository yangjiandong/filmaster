#-*- coding: utf-8 -*-
# Taken from http://www.djangosnippets.org/snippets/1655/
from django import template
from BeautifulSoup import BeautifulSoup, Comment
import re
import random
from django.conf import settings
from django.utils.translation import gettext_lazy as _

LANGUAGE_CODE = settings.LANGUAGE_CODE
import logging
logger = logging.getLogger(__name__)
register = template.Library()
ALLOWED_TAGS = getattr(settings, 'ALLOWED_TAGS', '')

def sanitize(value, allowed_tags):
    """Argument should be in form 'tag2:attr1:attr2 tag2:attr1 tag3', where tags
    are allowed HTML tags, and attrs are the allowed attributes for that tag.
    """
    js_regex = re.compile(r'[\s]*(&#x.{1,7})?'.join(list('javascript')))
    allowed_tags = allowed_tags + " " + ALLOWED_TAGS
    allowed_tags = [tag.split(':') for tag in allowed_tags.split()]
    allowed_tags = dict((tag[0], tag[1:]) for tag in allowed_tags)

    value = value.encode('ascii', 'xmlcharrefreplace')
    soup = BeautifulSoup(value)
    for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in soup.findAll(True):
        if tag.name not in allowed_tags:
            tag.hidden = True
        else:
            tag.attrs = [(attr, js_regex.sub('', val)) for attr, val in tag.attrs
                         if attr in allowed_tags[tag.name]]

    return soup.renderContents().decode('utf8')

register.filter(sanitize)

def spoiler(value):
    count = value.count('<spoiler>')
    for a in random.sample(xrange(10000), count):
        value = value.replace('<spoiler>', '<a onclick="javascript:toggle_reply('+str(a)+');" style="cursor: pointer;">'+str(_("See spoilers"))+' +</a><p id="reply-'+str(a)+'" class="spoiler" style="display:none;">',1).replace('</spoiler>','</p>',1)
    return value
register.filter(spoiler)

def remove_spoiler(value):
    """
       removes text tagged with <spoiler></spoiler> from text
    """

    value = value if value is not None else ''
    if "<spoiler>" in value:
        soup = BeautifulSoup(value)
        soup.spoiler.replaceWith("")
        return soup
    else:
        return value
register.filter(remove_spoiler)

