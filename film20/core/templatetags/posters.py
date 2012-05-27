import re
from django.template import Library, Node, Template, TemplateSyntaxError
from django.utils.translation import ugettext as _

from film20.utils.posters import get_image_path


import logging
logger = logging.getLogger(__name__)

register = Library()

class ResizedThumbnailNode(Node):
    def __init__(self, imdbobject, size):
        self.imdbobject = imdbobject
        self.size = size

    def render(self, context):
        self.size = [(i.resolve(context) if hasattr(i, 'resolve') else i) for i in self.size]
        
        imdbobject = self.imdbobject.resolve(context)

        return get_image_path(imdbobject, *self.size)

@register.tag('poster')
def Thumbnail(parser, token):
    bits = token.contents.split()
    if len(bits) < 3 or len(bits) > 4:
        raise TemplateSyntaxError, "You have to provide object and size spec !"
    if len(bits) == 3:
        size = (bits[1], 'auto')
        obj = bits[2]
    else:
        size = (bits[1:3])
        obj = bits[3]

    size = [re.match("\d+|auto", b) and b or parser.compile_filter(b) for b in size]

    return ResizedThumbnailNode(parser.compile_filter(obj), size)

