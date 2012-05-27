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

from django.template import loader
from django.template import Context
from django.http import HttpResponse
from django.views.decorators.cache import cache_page

from film20.moderation.registry import registry
from film20.moderation.models import ModeratedObject

#@cache_page( 60 * 5 )
def rss_feed( request, model, status=ModeratedObject.STATUS_UNKNOWN ):
    moderated_item = registry.get_by_name( model )
    if status is not ModeratedObject.STATUS_ACCEPTED \
       and not request.user.has_perm( moderated_item.permission ):
        return HttpResponse( 'Permission danied' )

    items = moderated_item.get_queryset( status )[:20]

    t = loader.get_template( moderated_item.get_rss_template_name() )
    c = Context( 
        { 'items': items, 'moderated_item': moderated_item, 'status': status } 
    )
    response = HttpResponse( mimetype='application/rss+xml' )
    response.write( t.render( c ) )
    
    return response
