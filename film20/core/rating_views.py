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
from django.template import RequestContext
from django import forms

from film20.config.urls import *
from film20.core import rating_helper
from film20.core.rating_form import RatingForm
from film20.utils.utils import *

import logging
logger = logging.getLogger(__name__)
    
def rate_films_fast_forward(request, ajax=None):
    if request.POST:
        if not request.user.is_authenticated():
            if ajax:
                return json_error('LOGIN')
            else:
                return HttpResponseRedirect(full_url('LOGIN') + '?next=%s&reason=vote' % request.path)
        form = rating_helper.handle_rating(RatingForm(request.POST),request.user)
        valid = form.is_valid()
        print "valid=" + str(valid)
        if ajax:
            print "ajax"
            return json_success() if valid else json_error("Hmm serwer nawalil?");

    films1 = []
    films2 = []
    for i in range(1, 6):
        film = rating_helper.get_next_film(request)
        films1.append(film)
        print "got film: " + film.title

    for j in range(1, 6):
        film = rating_helper.get_next_film(request)
        films2.append(film)
        print "got film: " + film.title

    context = {
        'films1': films1,
        'films2': films2
    }

    return render_to_response(
        templates['RATE_FILMS_FAST_FORWARD'], 
        context, 
        context_instance=RequestContext(request),
    )
