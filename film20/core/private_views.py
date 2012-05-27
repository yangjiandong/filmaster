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
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Q

from film20.config.urls import *
from film20.core.models import Object
from film20.core.models import Film
from film20.core.models import Person
from film20.core.models import Rating
from django.contrib.auth.models import User
from film20.core.models import Profile
from film20.core.film_helper import FilmHelper
#from film20.friends.friend_helper import FriendHelper

import logging
logger = logging.getLogger(__name__)

# TODO: registration

@login_required
def show_my_profile(request):
    """
    Shows the profile of the logged in user
    """
    # object to return
    favorite_films = None
    friend_invitations = None
    profile = None
    
    # get favorite movies
    film_helper = FilmHelper()
    favorite_films = film_helper.get_favorite_films(request.user)
    
    # get favorite actors
    
    # get favorite directors
    
    # get friend invitations
#    friend_helper = FriendHelper()
#    pending_received_invitations = friend_helper.get_pending_received_invitations(request.user)
#    pending_sent_invitations = friend_helper.get_pending_sent_invitations(request.user)
    
    # get profile data
    profile = request.user.get_profile()
    logger.debug("Profile description: " + unicode(profile.description))
    
    context = {
            'favorite_films': favorite_films,
            'pending_received_invitations':pending_received_invitations,
            'pending_sent_invitations':pending_sent_invitations,                 
            'profile': profile,            
            'user': request.user,
    }
    return render_to_response(
        templates['ACCOUNT'], 
        context,
        context_instance=RequestContext(request),
    )
