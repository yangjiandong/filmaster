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
from django import forms

SEARCH_TYPES = (
    ('all', _('All')),
    ('film', _('Film')),
    ('person', _('People')),
    ('user', _('Users')),
)

class SearchForm(forms.Form):
    search_phrase = forms.CharField(label=_("Phrase"), required=False, widget=forms.TextInput(attrs={'class':'text'}),)
    search_type = forms.ChoiceField(label=_("Search type"), required=True, choices=SEARCH_TYPES)
    
    def clean_search_phrase(self):
        self.search_phrase = self.cleaned_data["search_phrase"]
        if not self.search_phrase:
            raise forms.ValidationError(_("You have to enter search phrase to start search."))
        return self.cleaned_data["search_phrase"]
    
    
class SearchFilmForm(forms.Form):    
    title = forms.CharField(label=_("Title"), required=False, widget=forms.TextInput(attrs={'class':'text'}),)
    def clean_title(self):
        self.title = self.cleaned_data["title"]
        if ( (not self.title) | (self.title == '')):
            raise forms.ValidationError(_("You have to enter title to start film search."))
        return self.cleaned_data["title"]
    
class SearchPersonForm(forms.Form):
    person_name = forms.CharField(label=_("Person name"), required=False, widget=forms.TextInput(attrs={'class':'text'}),)
    person_surname = forms.CharField(label=_("Person surname"), required=False, widget=forms.TextInput(attrs={'class':'text'}),)
    
    def clean(self):        
        self.person_name = self.cleaned_data["person_name"]
        self.person_surname = self.cleaned_data["person_surname"]
        if ( (not self.person_name) & (not self.person_surname) ):            
            raise forms.ValidationError(_("You have to enter either person name or surname to start search."))
        return self.cleaned_data
