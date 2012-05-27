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
# Python
import logging

# Django
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.db import IntegrityError, connection
from django.views.generic.list import ListView

# Project
from film20.config.urls import *
from film20.utils.utils import *
from film20.filmbasket.models import *
from film20.filmbasket.forms import *
from film20.core.models import Film
from film20.core.film_views import show_film
import film20.settings as settings

logger = logging.getLogger(__name__)

@login_required
def add_to_basket(request, ajax=None):
    """
        Adds an item to basket.

        Warning: filmbasket_basketitem_user_id_key constraint may be violated if case the
                same method gets called twice with identical parameters and the function
                tries to insert a new rating twice. This is handled quietly, check
                http://jira.filmaster.org/browse/FLM-771 for details.
    """
    
    if (ajax!=None) & (ajax!='json'):
        raise Http404
    
    if not request.user.is_authenticated():
        if ajax:
            return json_error(reason="LOGIN")
        else:
            return HttpResponseRedirect(full_url("LOGIN"))
    
    the_film = None
    buttons_form = ButtonsForm(request.POST)
    
    if buttons_form.is_valid():
        film_id = buttons_form.cleaned_data['film_id']
        basket_action = buttons_form.cleaned_data['basket_action']
        
        try:
            the_film = Film.objects.get(id=film_id)
        except Film.DoesNotExist:
            logger.debug("Unknown film_id: " + unicode(film_id))
            raise Http404
            
        try:
            basket_item = BasketItem.objects.get(film=the_film, user=request.user)
        except BasketItem.DoesNotExist:
            basket_item = BasketItem(film=the_film, user=request.user)
    
        if basket_action == "add_to_wishlist":
            if (basket_item.wishlist==None) | (basket_item.wishlist!=BasketItem.DYING_FOR):
                logger.debug("Setting wishlist to BasketItem.DYING_FOR")
                basket_item.wishlist = BasketItem.DYING_FOR
            else:
                logger.debug("Setting wishlist to None")
                basket_item.wishlist = None
        elif basket_action == "add_to_shitlist":
            if (basket_item.wishlist==None) | (basket_item.wishlist!=BasketItem.NOT_INTERESTED):
                logger.debug("Setting wishlist to BasketItem.NOT_INTERESTED")
                basket_item.wishlist = BasketItem.NOT_INTERESTED
            else:
                logger.debug("Setting wishlist to None")
                basket_item.wishlist = None
        elif basket_action == "add_to_collection":
            if (basket_item.owned==None) | (basket_item.owned!=BasketItem.OWNED):
                logger.debug("Setting owned to BasketItem.OWNED")
                basket_item.owned = BasketItem.OWNED
            else:
                logger.debug("Setting owned to None")
                basket_item.owned = None
        else:
            logger.debug("Unknown option: " + unicode(basket_action))
            raise Http404

        try:
            basket_item.save()
            logger.debug("BasketItem saved")
        except IntegrityError:
            # Required to clear PostgreSQL's failed transaction
            # See http://jira.filmaster.org/browse/FLM-761
            logger.debug("BasketItem already saved - integrity error filmbasket_basketitem_user_id_key violated - closing connection!")
            connection.close()
        
        if ajax:
            logger.debug("Sending ajax response...")
            return json_success()
        else: 
            logger.debug("Sending HTTP response...")
            return HttpResponseRedirect(full_url("FILM")+the_film.permalink+"/")
    else:
        logger.debug("Form invalid!")
        try:
            if ajax:
                json_error("Buttons form invalid!")
            else:
                film_id = int(request.POST["film_id"])
                Film.objects.get(id=film_id)
                return show_film(request)
        except:
            raise Http404
