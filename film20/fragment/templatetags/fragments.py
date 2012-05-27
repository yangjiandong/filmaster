from django import template
from django.utils.safestring import mark_safe

from film20.utils import cache
from film20.fragment.models import Fragment

register = template.Library()

class FragmentNode( template.Node ):
    def __init__( self, key ):
        self.key = key
        
    def render( self, context ):
        return self.get_item_to_display()

    def get_fragments( self ):
        key = cache.Key( "fragments-set-%s" % self.key )
        fragments = cache.get( key )
        if fragments is None:
            fragments = Fragment.objects.filter( key=self.key )
            cache.set( key, fragments, cache.A_MONTH )

        return fragments

    def get_item_to_display( self ):
        fragments = self.get_fragments()
        count = len( fragments )
        if count > 0:
            if count == 1:
                f = fragments[0]

            else:
                key = cache.Key( "fragments-ld-%s" % self.key )
                last_displayed = cache.get( key )
                to_display = 0
                if last_displayed is not None:
                    to_display = last_displayed + 1
                    if to_display + 1 > count:
                        to_display = 0

                cache.set( key, to_display, cache.A_MONTH )
                
                f = fragments[to_display]

            return mark_safe( f.body )

        return ''


def fragment( parser, token ):
    try:
        tag_name, key = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError( "%s tag requires a single argument" % token.contents.split()[0] )

    return FragmentNode( key )

register.tag( fragment )
