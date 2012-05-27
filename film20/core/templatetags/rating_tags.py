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
from film20.utils.template import Library

from film20.config.urls import *
from film20.core.models import Film
from film20.core.models import Person
from film20.core.models import Rating
from film20.core import rating_helper
from film20.core.film_views import SHORT_REVIEW_FORM_ID

import logging
logger = logging.getLogger(__name__)

register = Library()

@register.simple_tag
def label_for_rating_type(rating_type):
    return rating_helper.get_rating_type_label(rating_type)
    
@register.inclusion_tag('rating/author_rating.html')
def author_rating(rating):
    
    label = rating_helper.get_rating_type_label(rating.type)

    votes_on = []
    votes_off = []
    
    for i in range(1, rating.rating+1):
        votes_on.append(i)
    
    for i in range(rating.rating+1, 11):
        votes_off.append(i)    
    
    return {            
            'label': label,
            'rating': rating,
            'votes_on': votes_on,
            'votes_off': votes_off,
        }

@register.inclusion_tag('rating/display_rating_form.html')
def display_rating_form(rating_object, the_object, url_string, already_rated=True, label=None):
    
    form_url = None
    if not label:
        label = rating_helper.get_rating_type_label(rating_object['type'])    
    
    # TODO: pass already rated for advanced forms
    logger.debug(unicode(url_string))
    logger.debug("already rated: " + unicode(already_rated))               
    
    form_url = full_url(url_string)
    if url_string != "RATE_FILMS":    
        form_url = form_url + the_object.parent.permalink + "/"    
    
    # TODO: generate random form ID
    return {            
            'rating_form' : rating_object['form'],
            'the_object' : the_object,
            'form_url' : form_url,
            'label' : label,
            'already_rated' : already_rated,
            'rating_type' : rating_object['type'],
        }

@register.new_inclusion_tag('rating/rating_form.html')
def rating_form(context, film_id=None, actor_id=None, director_id=None, type=Rating.TYPE_FILM):
    from film20.core.rating_form import SingleRatingForm
    request = context.get('request')
    return {
            'form': SingleRatingForm(None, request, initial={
                'film_id': film_id,
                'director_id': director_id,
                'actor_id': actor_id,
                'type': type,
                })
    }

@register.inclusion_tag('rating/display_short_review_form.html')
def display_short_review_form(the_form):    

    return {            
            'the_form' : the_form,
            'FORM_ID' : SHORT_REVIEW_FORM_ID, 
        }
