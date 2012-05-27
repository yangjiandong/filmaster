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
from django import template
from film20.config import *
from film20.core.models import Object
from film20.filmbasket.models import BasketItem

import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.simple_tag
def basket_title(type):
    if type ==  BasketItem.DYING_FOR:
        return _("Wishlist")
    elif type ==  BasketItem.NOT_INTERESTED:
        return _("Shitlist")    
    elif type == "OWNED":
        return _("Home collection")
    else:
        # TODO: exception??
        return _("Basket")

@register.simple_tag
def basket_feature_info(type):
    if type == BasketItem.DYING_FOR:
        return _("This is a list of movies you want to watch in the future.")
    elif type == BasketItem.NOT_INTERESTED:
        return _("This is a list of movies you do not want to watch and see in recommendations.")
    elif type == "OWNED":
        return _("This is a list of the movies you own.")
    else:
        # TODO: exception??
        return _("This is some totally unexpected list.")
