import re
from django.conf import settings
from django.template import Node

from film20.core.templatetags.movie import top_recommendations_all
from film20.utils.template import Library
register = Library()

@register.inclusion_tag('fbapp/recommended.html', takes_context=True)
def fbapp_recommended(context):

    POPULAR_FILMS_NUMBER = getattr(settings,
            'POPULAR_FILMS_MAIN_PAGE_NUMBER')

    all_films = top_recommendations_all(context, POPULAR_FILMS_NUMBER)

    return{
        'all_films': all_films,
    }

class RecomTemplate( Node ):
    def __init__( self, count, var_name ):
        self.count = int( count )
        self.var_name = var_name

    def render( self, context ):
        context[self.var_name] = top_recommendations_all( context, self.count )
        return ''

def get_fbapp_recommended( parser, token ):
    try:
        tag_name, arg = token.contents.split( None, 1 )
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    count, var_name = m.groups()
    return RecomTemplate( count, var_name )

register.tag( get_fbapp_recommended )
