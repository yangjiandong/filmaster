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
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect        
from django.template import RequestContext
from django.shortcuts import render_to_response

from film20.event.models import Event, Nominated
from film20.core.models import Film, Person
from film20.core.rating_form import RatingForm
from film20.core import rating_helper
from film20.utils.utils import *
from film20.config.urls import full_url

from random import shuffle
from itertools import groupby

import logging
logger = logging.getLogger(__name__)

def show_event(request, permalink, ajax=None):
    event = get_object_or_404(Event,permalink = permalink)
    nominated = Nominated.objects.with_rates(event)
    for n in nominated:
        if n.film_id:
            n.film = Film.get(id=n.film_id)
        if n.person_id:
            n.person = Person.get(id=n.person_id)
    categories = []
    for type, items in groupby(nominated, lambda n: n.oscar_type):
        items = list(items)
        if event.event_status == Event.STATUS_OPEN:
            shuffle(list(items))
        if items:
            categories.append({
                'name': items[0].get_category_name(),
                'nominated': items,
            })

    ctx = {
        'event': event,
        'categories': categories,
    }

    return render_to_response('event/event.html', ctx, context_instance=RequestContext(request))
