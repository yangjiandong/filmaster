import re
from django import template
from django.core import urlresolvers

from film20.demots.models import Demot

register = template.Library()

class CountTagNode( template.Node ):
    def __init__( self, count, var_name ):
        self.count = int( count )
        self.var_name = var_name
        
    def render( self, context ):
        context[self.var_name] = self.get_query_set()
        return ''

    def get_query_set( self ):
        pass

def parse_count_tag( parser, token ):
    try:
        tag_name, arg = token.contents.split( None, 1 )
    except ValueError:
        raise template.TemplateSyntaxError( "%r tag requires arguments " % token.contents.split()[0] )
    m = re.search( r'(\d+) as (\w+)', arg )
    if not m:
        raise template.TemplateSyntaxError( "%r tag had invalid arguments" % tag_name )
    count, var_name = m.groups()
    return int( count ), var_name

class LatestsDemots( CountTagNode ):
    def get_query_set( self ):
        return Demot.objects.all()[:self.count]

def get_latest_demots( parser, token ):
    return LatestsDemots( *parse_count_tag( parser, token ) )

register.tag( get_latest_demots )
