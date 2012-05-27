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
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response, redirect
from django.contrib.auth.decorators import login_required

from film20.moderation.registry import registry
from film20.moderation.models import ModeratedObject
from film20.moderation.items import ModeratorTool, ModerationException
from film20.moderation.forms import RejectForm
from film20.moderation.feeds import rss_feed

@login_required
def index( request ):
    
    moderated_items = registry.get_by_user( request.user )

    first_with_items = None
    for moderated_item in moderated_items['items']:
        if first_with_items is None and moderated_item.get_not_moderated().count() > 0:
            first_with_items = moderated_item
            break

    if first_with_items is None:
        first_with_items = moderated_items['items'][0] if len( moderated_items['items'] ) > 0 else None

    return render_to_response( "moderation/index.html", {
        "moderated_item": first_with_items,
        "moderated_items": moderated_items['items'],
        "moderator_tools": moderated_items['tools'],
    }, context_instance=RequestContext( request ) )

@login_required
def moderate_item( request, model ):
    moderated_item = registry.get_by_name( model )
    if moderated_item is None:
        raise Http404

    if request.user.has_perm( moderated_item.permission ):
        if isinstance( moderated_item, ModeratorTool ):
            return moderated_item.get_view( request )

        template = "moderation/index.html"
        moderated_items = registry.get_by_user( request.user )
        args = {
            "moderated_item": moderated_item,
            "moderated_items": moderated_items['items'],
            "moderator_tools": moderated_items['tools'],
        }
        if request.method == 'POST':
            try:
                if 'reject' in request.POST and not 'confirmed' in request.POST:
                    item_id = request.POST.get( 'id', None )
                    if item_id is None:
                        raise ModerationException( "Unknown item ..." )

                    template = "moderation/reject.html"
                    args['form'] = RejectForm()
                    args['item'] = moderated_item.get_by_pk( int( item_id ) )

                else:
                    process_action( request, moderated_item )

            except ModerationException, e:
                request.user.message_set.create( message=str( e ) )

        return render_to_response( template, args, context_instance=RequestContext( request ) )

    else:
        # redirect to moderation panel ...
        request.user.message_set.create( message="Permission danied!" )
        return redirect( "moderation" )

@login_required
def get_feed( request, model, status=ModeratedObject.STATUS_UNKNOWN ):
    return rss_feed( request, model, status )

def process_action( request, moderated_item ):
    user = request.user
    item_id = request.POST.get( 'id', None )
    
    if item_id is None:
        raise ModerationException( "Unknown item ..." )
    
    # if item doesn't exits should raise Exception
    item = moderated_item.get_by_pk( int( item_id ) )
    
    if 'reject' in request.POST:
        reject( moderated_item, item, user, request.POST.get( 'reason', None ) )

    elif 'accept' in request.POST: 
        accept( moderated_item, item, user, **request.POST )

    else: 
        raise ModerationException( "Unknown action ..." )

def accept( moderated_item, item, user, **kwargs ):
    if moderated_item.can_accept( item, user ):
        moderated_item.accept_item( item, user, **kwargs )

def reject( moderated_item, item, user, reason ):
    if moderated_item.can_reject( item, user ):
        moderated_item.reject_item( item, user, reason )

