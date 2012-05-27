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

import logging
logger = logging.getLogger(__name__)

from django import forms
from django.utils.translation import gettext_lazy as _

import film20.settings as settings
from film20.core.object_helper import ObjectTagForm

# constants
MIN_CHARACTERS_SHORT_REVIEW = getattr(settings, "MIN_CHARACTERS_SHORT_REVIEW", 10)
MAX_CHARACTERS_SHORT_REVIEW = getattr(settings, "MAX_CHARACTERS_SHORT_REVIEW", 1000)
MAX_CHARACTERS_FILM_TITLE = getattr(settings, "MAX_CHARACTERS_FILM_TITLE", 255)
MAX_CHARACTERS_FILM_DESCRIPTION = getattr(settings, "MAX_CHARACTERS_FILM_DESCRIPTION", 15000)

class FilmLocalizedTitleForm(forms.Form):
    localized_title = forms.CharField(label=_("Localized title"), max_length=120, widget=forms.TextInput({'class':'text'}),)
    
    def clean_localized_title(self):
        localized_title = self.cleaned_data.get('localized_title', '')
        if localized_title:       
            # empty is not good
            if len(localized_title)==0:
                raise forms.ValidationError(_("Title cannot be an empty strong!"))
            # cannot be too long
            elif len(localized_title)>MAX_CHARACTERS_FILM_TITLE:
                raise forms.ValidationError(_("Title cannot be longer than %s characters!" % MAX_CHARACTERS_FILM_TITLE))
            else:                 
                return localized_title
        else:
            return None    
        
class FilmDescriptionForm(forms.Form):
    description = forms.CharField(label=_("Synopsis"), widget=forms.Textarea({'cols': '40', 'rows': '4'}), required=True) 
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if description:       
            # empty is not good
            if len(description)==0:
                raise forms.ValidationError(_("Description cannot be an empty string!"))
            # cannot be too long
            elif len(description)>MAX_CHARACTERS_FILM_DESCRIPTION:
                raise forms.ValidationError(_("Description cannot be longer than %s characters!" % MAX_CHARACTERS_FILM_DESCRIPTION))
            else:                 
                return description
        else:
            return None  
        
class ShortReviewForm(forms.Form):
        
    edit_id = forms.CharField(widget=forms.HiddenInput, required=False)
    object_id = forms.CharField(widget=forms.HiddenInput, required=False)
    review_text = forms.CharField(widget=forms.Textarea({'class':'short_review-textarea'}), required=False)

    __empty = False

    def is_empty(self):
        return self.__empty
    
    def clean_object_id(self):
        object_id = self.cleaned_data.get('object_id', '')
        if object_id:        
            try:
                int(object_id)
                return int(object_id)
            except ValueError:            
                raise forms.ValidationError(_("object_id must be integer!"))
        else:
            return None
        
    def clean_edit_id(self):
        edit_id = self.cleaned_data.get('edit_id', '')
        if edit_id:        
            try:
                int(edit_id)
                return int(edit_id)
            except ValueError:            
                raise forms.ValidationError(_("edit_id must be integer!"))
        else:
            return None
    
    def clean_review_text(self):
        review_text = self.cleaned_data.get('review_text', '')

        if len(review_text)==0:
            self.__empty = True
            return review_text
        elif len(review_text)>MAX_CHARACTERS_SHORT_REVIEW:
            raise forms.ValidationError(_("Review cannot be longer than %s characters!" % MAX_CHARACTERS_SHORT_REVIEW))
        # cannot be too short          
        elif len(review_text)<MIN_CHARACTERS_SHORT_REVIEW:
            raise forms.ValidationError(_("Review cannot be shorter than %s characters! This is a review, damn it!" % MIN_CHARACTERS_SHORT_REVIEW))
        else:                 
            return review_text
