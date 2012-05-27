# -*- coding: utf-8 -*-
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
import decimal
from django.utils.translation import gettext_lazy as _
from django import forms
from film20.tagging.forms import TagField
from film20.core.models import Rating
from film20.core import rating_helper
from film20.core.forms import do_clean_related_person
from film20.utils.slughifi import slughifi

import logging
logger = logging.getLogger(__name__)

def get_rating_tuple(type):
    label = rating_helper.get_rating_type_label(type)
    return (slughifi(str(label)), str(label))
    
def get_rating_types_to_display():
    
    types = []
    types.append( get_rating_tuple(Rating.TYPE_FILM) )          
    types.append( get_rating_tuple(Rating.TYPE_EXTRA_DIRECTORY) )
    types.append( get_rating_tuple(Rating.TYPE_EXTRA_SCREENPLAY) )
    types.append( get_rating_tuple(Rating.TYPE_EXTRA_ACTING) )
    types.append( get_rating_tuple(Rating.TYPE_EXTRA_SPECIAL_EFFECTS) )
    types.append( get_rating_tuple(Rating.TYPE_EXTRA_EDITING) )
    types.append( get_rating_tuple(Rating.TYPE_EXTRA_MUSIC) )
    types.append( get_rating_tuple(Rating.TYPE_EXTRA_CAMERA) )
    types.append( get_rating_tuple(Rating.TYPE_EXTRA_NOVELTY) )
            
    return types

def get_rating_type_as_int(type_as_str):
    # pl
    if (type_as_str == "film") | (type_as_str == None): 
        return Rating.TYPE_FILM
    elif type_as_str == "rezyseria":
        return Rating.TYPE_EXTRA_DIRECTORY
    elif type_as_str == "scenariusz":
        return Rating.TYPE_EXTRA_SCREENPLAY
    elif type_as_str == "aktorstwo":
        return Rating.TYPE_EXTRA_ACTING
    elif type_as_str == "efekty-specjalne":
        return Rating.TYPE_EXTRA_SPECIAL_EFFECTS
    elif type_as_str == "montaz":
        return Rating.TYPE_EXTRA_EDITING
    elif type_as_str == "muzyka":
        return Rating.TYPE_EXTRA_MUSIC
    elif type_as_str == "zdjecia":
        return Rating.TYPE_EXTRA_CAMERA
    elif type_as_str == "innowacyjnosc":
        return Rating.TYPE_EXTRA_NOVELTY
    # en
    elif (type_as_str == "film") | (type_as_str == None): 
        return Rating.TYPE_FILM
    elif type_as_str == "direction":
        return Rating.TYPE_EXTRA_DIRECTORY
    elif type_as_str == "screenplay":
        return Rating.TYPE_EXTRA_SCREENPLAY
    elif type_as_str == "acting":
        return Rating.TYPE_EXTRA_ACTING
    elif type_as_str == "special-effects":
        return Rating.TYPE_EXTRA_SPECIAL_EFFECTS
    elif type_as_str == "editing":
        return Rating.TYPE_EXTRA_EDITING
    elif type_as_str == "music":
        return Rating.TYPE_EXTRA_MUSIC
    elif type_as_str == "cinematography":
        return Rating.TYPE_EXTRA_CAMERA
    elif type_as_str == "innovativeness":
        return Rating.TYPE_EXTRA_NOVELTY
    return None             
        
from film20.recommendations.recom_helper import FILMASTER_TYPES, FILMASTERS_ALL
from film20.recommendations.recom_helper import FILMASTERS_SORT_BY, FILMASTERS_SORT_COMMON_TASTE
class FilmastersForm(forms.Form):
    min_common_films = forms.CharField(label=_("Min. common films"), 
                                       max_length=4, 
                                       widget=forms.TextInput({'class':'text'}),)
    sort_by = forms.ChoiceField(label=_('Sort by'), required=True,
        choices=FILMASTERS_SORT_BY, initial=FILMASTERS_SORT_COMMON_TASTE,
        widget=forms.Select(choices=FILMASTERS_SORT_BY))
    
    def clean_min_common_films(self):        
        min_common_films = self.cleaned_data.get('min_common_films', '')     
        try:
            int(min_common_films)
        except ValueError:
            raise forms.ValidationError(_("Min common films must be an integer!"))
        return int(min_common_films)
    
class TopUsersForm(FilmastersForm):
    filmaster_type = forms.ChoiceField(label=_('Filter Filmasters'), required=True,
        choices=FILMASTER_TYPES, initial=FILMASTERS_ALL,
        widget=forms.Select(choices=FILMASTER_TYPES))    

import re
def validate_tags(tags):
    tags = tags.strip()
    tags = tags.rstrip(",")
    if (tags is not None) & (tags != ''):
        taglist = tags.split(",")
        for tag in taglist:
            tag = tag.strip()
            # check if each tag is a simple string (spaces allowed)
            m = re.match(u"([a-zA-Z0-9ĄĘŚĆŻŹŁÓĆŃąęśćżźłóćń\s-]+)$", tag)
            if m is None:
#                print "ERROR: " + tag + " "
                return False
            else:
                extracted = m.group(1)
                if extracted is None:
#                    print "ERROR: " + tag + " "
                    return False
                else:
#                    print "TAG OK: " + extracted + " "
                    pass
            pass
            
    return True

class FakeFilmSpecsForm():
    year_from = None
    year_to = None
    tags = None
    related_director_as_object = None
    related_director_as_string = None
    related_actor_as_object = None
    related_actor_as_string = None
    popularity = None
    
    def __init__(self, year_from=None, year_to=None, tags=None, related_director_as_object=None, related_director_as_string=None, related_actor_as_object=None, related_actor_as_string=None, popularity=None):
        self.year_from = year_from
        self.year_to = year_to

        self.tags = tags

        # strip the ", " from the end of the tags string (if present)
        if self.tags != None:
            self.tags = self.tags.strip()
            self.tags = self.tags.rstrip(",")

        self.related_director_as_object = related_director_as_object
        self.related_director_as_string = related_director_as_string
        self.related_actor_as_object = related_actor_as_object
        self.related_actor_as_string = related_actor_as_string
        self.popularity = popularity

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        result = validate_tags(tags)
        if not result:
            raise forms.ValidationError(_("Tags have to be comma separated!"))
        else:
            return tags

    def is_empty_form(self):
        # TODO: why is self.related_director_as_object not None but ''? Investigate! 
        return (self.popularity == None) & ((self.related_director_as_object == None) | (self.related_director_as_object == '')) & (self.tags == None) & (self.year_to == None) & (self.year_from == None)
    
class FilmSpecsForm(forms.Form):
    year_from = forms.CharField(
        label=_("From (year)"), 
        max_length=4, 
        widget=forms.TextInput({'class':'text'}),
        required=False,)
    year_to = forms.CharField(
        label=_("To (year)"), 
        max_length=4, 
        widget=forms.TextInput({'class':'text'}),
        required=False,)
    related_director = forms.CharField(
        label=_("Director"), 
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'size':'53', 'class':'text'}))
    related_actor = forms.CharField(
        label=_("Actor"), 
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'size':'53', 'class':'text'}))
    
    tags = TagField(label=_("Tags"), max_length=255, widget=forms.TextInput({'class':'text'}),required=False,)
    popularity = forms.CharField(
        label=_("Min. votes"), 
        max_length=4, 
        widget=forms.TextInput({'class':'text'}),
        required=False,)
    
    def clean_related_director(self):
        return do_clean_related_person(self, related_person_str='related_director')
        
    def clean_related_actor(self):
        return do_clean_related_person(self, related_person_str='related_actor')

    def clean_year_from(self):        
        year = self.cleaned_data.get('year_from', '')
        if year == None:
            return None     
        elif year.strip()=='':
            return None
        year_int = -1
        try:
            year_int = int(year)
        except ValueError:
            raise forms.ValidationError(_("Year must be an integer!"))
        
        if year_int < 1850:
            raise forms.ValidationError(_("Year must be after 1850!"))
        elif year_int > 2020:
            raise forms.ValidationError(_("Year must be before 2020!"))            
            
        return year_int
    
    def clean_year_to(self):        
        year = self.cleaned_data.get('year_to', '')
        if year == None:
            return None     
        elif year.strip()=='':
            return None
        year_int = -1
        try:
            year_int = int(year)
        except ValueError:
            raise forms.ValidationError(_("Year must be an integer!"))
        
        if year_int < 1850:
            raise forms.ValidationError(_("Year must be after 1850!"))
        elif year_int > 2020:
            raise forms.ValidationError(_("Year must be before 2020!"))            
            
        return year_int

    def clean_popularity(self):        
        popularity = self.cleaned_data.get('popularity', '')
        if popularity == None:
            return None     
        elif popularity.strip()=='':
            return None
        popularity_int = -1
        try:
            popularity_int = int(popularity)
        except ValueError:
            raise forms.ValidationError(_("The value must be an integer!"))

        if popularity_int < 0:
            raise forms.ValidationError(_("The number can't be negative!"))

        return popularity_int

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        result = validate_tags(tags)
        if not result:
            raise forms.ValidationError(_("Tags have to be comma separated!"))
        else:
            return tags

from .models import RecommendationVote

class RecommendationVoteForm(forms.Form):

    film_id = forms.IntegerField(widget=forms.HiddenInput)
    vote = forms.ChoiceField(choices=RecommendationVote.VOTE_CHOICES, widget=forms.RadioSelect, required=False)

    def __init__(self, data, user, film=None):
        self.user = user
        initial = {}
        if film:
            initial['film_id'] = film.id
        if not data:
            try:
                vote = RecommendationVote.objects.get(user=user, film=film)
                initial['vote'] = vote.vote
            except RecommendationVote.DoesNotExist, e:
                pass
        super(RecommendationVoteForm, self).__init__(data, initial=initial)

    def save(self, **kw):
        ratings = Rating.get_user_ratings(self.user)
        number_of_ratings = len(ratings)
        if number_of_ratings:
            average_rating = decimal.Decimal(sum(ratings.values())) / number_of_ratings
        else:
            averate_rating = None
        ratings_based_prediction = None
        traits_based_prediction = None

        film_id = self.cleaned_data['film_id']
        vote = self.cleaned_data['vote'] or None
        
        defaults = {
                'vote': vote,
                'average_rating': average_rating,
                'number_of_ratings': number_of_ratings,
                'ratings_based_prediction': ratings_based_prediction,
                'traits_based_prediction': traits_based_prediction,
        }
        defaults.update(kw)
        vote, created = RecommendationVote.objects.get_or_create(user=self.user, film_id=film_id, defaults=defaults)
        if not created:
            vars(vote).update(defaults)
            vote.save()
        return vote
