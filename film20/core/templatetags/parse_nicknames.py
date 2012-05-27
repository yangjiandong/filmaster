import re

from django import template
from django.utils.safestring import mark_safe

from film20.utils.nicknames_parser import NicknamesParser

register = template.Library()

@register.filter
def parse_nicknames( text ):
    parser = NicknamesParser()
    return mark_safe( parser.parse( text ) )
