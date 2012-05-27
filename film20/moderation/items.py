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

from django.http import Http404
from django.core.urlresolvers import reverse
from django.utils.translation import gettext_lazy as _

from film20.moderation.models import ModeratedObject


class ModerationException( Exception ):
    pass

class ModeratedItem( object ):
    name = None
    model = None
    permission = None

    template_name = None
    item_template_name = None

    rss_template_name = None

    def get_name( self ):
        """
        must return unigue moderated item name 
        """
        if self.name is None:
            self.name = "%s-%s" % ( self.model._meta.app_label, \
                             self.model._meta.module_name )
        return self.name

    def get_absolute_url( self ):
        """
        return moderation absolute url
        """
        return reverse( "moderate-item", args=[ self.get_name() ] )

    def get_by_pk( self, id ):
        """
        return item by id
        """
        return self.model._default_manager.get( pk=id )

    def get_verbose_name( self ):
        """
        return verbose name
        """
        return self.model._meta.verbose_name

    def get_verbose_name_plural( self ):
        """
        return verbose name plural
        """
        return self.model._meta.verbose_name_plural

    def get_queryset( self, status ):
        """
        Get the default QuerySet for status

            - ModeratedObject.STATUS_UNKNOWN
            - ModeratedObject.STATUS_ACCEPTED
            - ModeratedObject.STATUS_REJECTED
        """
        raise NotImplementedError

    def get_not_moderated( self ):
        """
        get not verified objects
        """
        return self.get_queryset( ModeratedObject.STATUS_UNKNOWN )

    def get_template( self ):
        """
        returns list template
        """
        if self.template_name is None:
            self.template_name = "moderation/list.html"
        
        return self.template_name

    def get_rss_template_name( self ):
        """
        returns rss template
        """
        if self.rss_template_name is None:
            self.rss_template_name = "moderation/rss.xml"
        
        return self.rss_template_name

    def get_item_template( self ):
        """
        return template to display item on list
        """
        if self.item_template_name is None:
            self.item_template_name = "moderation/items/%s/record.html" % \
                        ( self.get_name() )

        return self.item_template_name

    def can_accept( self, item, user ):
        """
        implement custom logic to validate that user can accept item
        """
        return user.has_perm( self.permission )

    def can_reject( self, item, user ):
        """
        implement custom logic to validate that user can reject item
        """
        return user.has_perm( self.permission )

    def accept_item( self, item, user, **kwargs ):
        """
        if you not using ModeratedObject you must implement this method
        """
        raise NotImplementedError

    def reject_item( self, item, user, reason=None ):
        """
        if you not using ModeratedObject you must implement this method
        """
        raise NotImplementedError


class ModeratedObjectItem( ModeratedItem ):
    def __init__( self, model, permission, name=None, template_name=None, \
                 item_template_name=None, rss_template_name=None ):
        if not issubclass( model, ModeratedObject ):
            raise ModerationException( "model must be instance of ModeratedObject" )

        self.model = model
        self.permission = permission
        self.name = name
        self.template_name = template_name
        self.item_template_name = item_template_name
        self.rss_template_name = rss_template_name

    def get_queryset( self, status ):
        return self.model._default_manager.filter( moderation_status=status )

    def accept_item( self, item, user, **kwargs ):
        if self.can_accept( item, user ):
            item.accept( user, **kwargs )
        
        else: raise ModerationException( _( "Permission denied!" ) )

    def reject_item( self, item, user, reason=None ):
        if self.can_reject( item, user ):
            item.reject( user, reason )

        else: raise ModerationException( _( "Permission denied!" ) )


class ModeratorTool( ModeratedItem ):
    verbose_name = ""

    def get_view( self, request ):
        raise Http404

    def get_verbose_name( self ):
        return self.verbose_name


