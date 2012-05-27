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

from film20.config.urls import *

#import logging

register = template.Library()

@register.simple_tag
def tags_with_pipes(tags_with_commas):
    l1 = tags_with_commas.split( "," )
    new_tags = []
    for tag in l1:
        new_tags.append('<a href="/' + urls['TAG'] + '/' + tag.strip() + '/">' + tag + '</a>')
        
    tags_with_pipes_str = " | ".join(new_tags)
    return tags_with_pipes_str

# TODO: form_ids
@register.inclusion_tag('film/display_edit_tags_form.html')
def display_edit_tags_form(object_type, permalink, form, tags, is_edit, can_edit_tags):
            
    full_permalink = full_url(object_type) + permalink + "/"
    
    return {            
            'full_permalink' : full_permalink, 
            'form' : form,
            'is_edit' : is_edit,
            'tags' : tags,
            'can_edit_tags' : can_edit_tags,
        }

def get_is_edit(edit_or_display):
    if edit_or_display=="edit":
        return True
    else:
        return False
    
@register.inclusion_tag('widgets/review_description.html')
def review_description(review, words=None, skip_if_none=False, strip_html=False):

    if words == "False":
        words = None
    if skip_if_none == "False":
        skip_if_none = False
    if strip_html == "True":
        strip_html = True

    return {
            'review': review,
            'words': words,
            'skip_if_none': skip_if_none,
            'strip_html': strip_html,
        }

@register.inclusion_tag('film/localized_title.html')
def localized_title(the_film, no_slash=False, comma=False):            
    return {            
            'the_film': the_film,
            'slash': not no_slash, 
            'comma': comma,
        }

@register.inclusion_tag('movies/movie/directors.html')
def directors(directors, short=None):
    return {
            'directors': directors,
            'short':short,
        }

@register.simple_tag
def first_letter(title):
    return title[0]

@register.filter
def format_score(score, default=None):
    if default is None or score:
        score = float(score)
        return "%.1f" % (score < 1 and 1 or score>10 and 10 or score)
    return default
