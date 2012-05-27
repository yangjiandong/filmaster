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
from django.utils.translation import gettext_lazy as _, gettext
from django import template
from django.conf import settings

from film20.config.urls import *
from film20.core.models import Film, Person, Rating
from film20.core.rating_form import SingleRatingForm
from film20.utils.template import Library

import logging
logger = logging.getLogger(__name__)

register = Library()

def _get_films(context, person, title, id, **kw):
    occupation = False
    request = context['request']
    user = request.user

    films = Film.objects.filter(**kw)
    films = films.order_by("-release_year").distinct().select_related()
    films = list(films)
    if films:
        if 'directors' in kw:
            occupation = 'director'
        if 'character__person' in kw:
            occupation = 'actor'

    return {
        'user': user,
        'person': person,
        'title':title,
        'id':id,
        'films':films,
        'occupation': occupation,
    }

@register.inclusion_tag('person/films.html', takes_context=True)
def person_films_directed(context, person):
    return _get_films(context, person, _("Films Directed"), "films_directed", directors=person)

@register.inclusion_tag('person/films.html', takes_context=True)
def person_films_played(context, person):
    return _get_films(context, person, _("Films Played"), "films_played", character__person=person)

@register.new_inclusion_tag('person/score.html')
def actor_score(context, person):
    return {
        'title': _("Actor"),
        'id': "actor_score",
        'person': person,
        'average': person.average_actor_score(),
        'rating_form_type': Rating.TYPE_ACTOR,
        'actor_id': person.id,
        'director_id': None,
    }

@register.new_inclusion_tag('person/score.html')
def director_score(context, person):
    return {
        'title': _("Director"),
        'id': "director_score",
        'person': person,
        'average': person.average_director_score(),
        'rating_form_type': Rating.TYPE_DIRECTOR,
        'actor_id': None,
        'director_id': person.id,
    }
