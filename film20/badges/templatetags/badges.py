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
import random
import logging
import pytz, datetime

# Django
from django.utils.translation import gettext_lazy as _, gettext
from django.contrib.auth.models import User
from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

# Project
from film20.config.urls import *
from film20.showtimes.models import Channel, TYPE_TV_CHANNEL, TYPE_CINEMA
from film20.showtimes.showtimes_helper import collect_unique_films, \
        get_theaters, get_tv_channels, get_today
from film20.core.models import Rating, Film
from film20.core.rating_form import FilmRatingForm, SimpleFilmRatingForm
from film20.core.film_helper import FilmHelper
from film20.filmbasket.models import BasketItem
from film20.recommendations.recom_helper import RecomHelper
from film20.utils import cache_helper as cache
from film20.utils.cache_helper import CACHE_ACTIVITIES, CACHE_HOUR, A_DAY

logger = logging.getLogger(__name__)

from film20.utils.template import Library
register = Library()

from film20.utils.cache import cache_query
from film20.badges.models import Goal

@register.widget('badges/user_progress.html', embed=True)
def user_progress(request):
    return {
            'goal': request.goal,
    }
