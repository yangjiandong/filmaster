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
from django import template
from django.contrib.auth.models import User


from film20.core.models import Film
from film20.core.models import Person
from film20.utils.texts import normalized_text, text_letters, text_root_normalized
from film20.search.forms import model_choices

register = template.Library()

def get_item_type( context, item ):
    # this is a stupid fix to make search work and not throw
    # AttributeError: 'NoneType' object has no attribute 'model_name'
    # TODO: needs to be fixed 
    if item is None:
        return {}
    elif item.model_name == 'film': item_type = 'FILM'
    elif item.model_name == 'person': item_type = 'PERSON'
    elif item.model_name == 'user': item_type = 'USER'
    elif item.model_name == 'post': item_type = 'POST'
    elif item.model_name == 'shortreview': item_type = 'SHORT_REVIEW'
    elif item.model_name == 'threadedcomment': item_type = 'COMMENT'
    else: item_type = 'UNKNOWN'

    return {
        'item' : item.object,
        'h_item': item, # haystack item
        'item_type': item_type,
        'request': context['request']
    }

@register.inclusion_tag( 'search/display_single_search_result.html', takes_context=True )
def display_single_search_result( context, item ):
    return get_item_type( context, item )

@register.filter
def normalize( value ):
    return normalized_text( value )

@register.filter
def root_normalize( value ):
    return text_root_normalized( normalized_text( value ) )

@register.filter
def letters( value ):
    return text_letters( normalized_text( value ) )

@register.filter
def to_verbose_name( value ):
    for key, name in model_choices():
        if key == value: return name
    return value # probably never
