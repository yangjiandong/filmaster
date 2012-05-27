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
from django.db.models import Q
from django import forms

from film20.tagging.forms import TagField

from film20.core.models import Film
from film20.core.models import Person
from film20.core.models import Character
from film20.core.models import Rating
from film20.core.models import RatingComparator

import logging
logger = logging.getLogger(__name__)

class ObjectTagForm(forms.Form):
    tags = TagField(label=_("Tags"), max_length=255, widget=forms.TextInput({'class':'text'}),)
    
class UserComparator:    
    score = None
    
    def __init__(self, score=None):
        self.score = score
    
class ObjectHelper:
    """
    A ``Helper`` object for objects, to facilitate common static operations
    """
    
    def get_object_tag_form(self, the_object, POST=None):
        if POST==None:
            return ObjectTagForm(
                initial = {
                    'tags': the_object.get_tags(),
                }
            )
        else:
            return ObjectTagForm(POST)
        
    def handle_edit_tag(self, the_object, the_form):
        """
        Handles the tag editing form.
        """
        is_valid = the_form.is_valid()
        
        if is_valid:     
            tags = the_form.cleaned_data['tags']
            the_object.save_tags(tags)
            logger.debug("Tags saved: " + tags)
        
        return is_valid            

    def is_set(self, param):
        try:
            if int(param)==1:
                return True
            else:
                return False
        except ValueError:
            return False
