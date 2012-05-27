import re
import BeautifulSoup

from django.template import Library
from django.utils.safestring import mark_safe

register = Library()

def nofollow( value ):
    soup = BeautifulSoup.BeautifulSoup( value )
    for a in soup.findAll( 'a' ):
        a['rel'] = 'nofollow'
    return mark_safe( soup.renderContents() )

def noprotocol( value ):
    soup = BeautifulSoup.BeautifulSoup( value )
    for a in soup.findAll( 'a' ):
        tokens = a.string.split('://')
        if len( tokens ) > 1:
            a.string = tokens[len( tokens ) - 1]
    return mark_safe( soup.renderContents() )

register.filter( nofollow )
register.filter( noprotocol )
