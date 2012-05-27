from django.db import DEFAULT_DB_ALIAS
from django.utils.html import escape
from django.utils.text import capfirst
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.contrib.admin.util import NestedObjects

DEFAULT_TO_UPDATE = [
    'core_rating', 
    'core_character',
    'core_shortreview',
    'filmbasket_basketitem',
    'useractivity_useractivity', 
]

def get_related_objects( obj, to_update=DEFAULT_TO_UPDATE ):
    collector = NestedObjects( using=DEFAULT_DB_ALIAS )
    collector.collect( obj )
    perms_needed = set()

    def format_callback( o ):
        opts   = o._meta
        key    = '%s_%s' % ( opts.app_label, opts.object_name.lower() )
        to_delete =  key not in to_update

        try:
            admin_url = reverse( 'admin:%s_%s_change' % ( opts.app_label, opts.object_name.lower() ),
                                None, ( o._get_pk_val() ,) )
        except:
            return mark_safe( u'%s%s: %s%s' % ( '<strike>' if to_delete else '', capfirst( opts.verbose_name ), force_unicode( o ), '</strike>' if to_delete else '' ) )

        try:
            name = escape( str( o ) )
        except Exception, e:
            print e
            name = 'None'

        return mark_safe( u'%s%s: <a href="%s">%s</a>%s' %
                             ( '<strike>' if to_delete else '', escape( capfirst( opts.verbose_name ) ),
                              admin_url, name, '</strike>' if to_delete else '' ) )


    return collector.nested(format_callback)


class Preview( object ):
    def __init__( self, request, format_callback=None ):
        self.request = request
        self._items = {}
        self._format_callback = format_callback if format_callback else self._default_formatter 

    def add_item( self, category, item, msg=None ):
        if not self._items.has_key( category ):
            self._items[category] = { 'msg': msg, 'items': [] }
        self._items[category]['items'].append( self._format_callback( item, self.request ) )

    def all( self ):
        return self._items

    def _default_formatter( self, obj ):
        return str( obj )
