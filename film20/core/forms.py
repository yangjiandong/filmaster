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
from django.forms.util import ErrorList
from django.utils.translation import string_concat

from film20.search import search_person

from film20.utils.slughifi import slughifi
import logging
logger = logging.getLogger(__name__)

def get_related_people_as_comma_separated_string(related_people):
    related_names = '' 
    for related_name in related_people:
        related_names = related_names + unicode(related_name) + ", "
    related_names = related_names.rstrip(", ")
    return related_names
 
def do_clean_related_person(self, related_person_str='related_person'):
    related = []
    related_person_form_data = self.cleaned_data[related_person_str]
    if isinstance(related_person_form_data, (list, tuple)):
        return related_person_form_data
    if len(related_person_form_data) ==0:
        self.cleaned_data[related_person_str] == ""
        return self.cleaned_data[related_person_str]
    else:
        related_person_form_data = related_person_form_data.replace(", ",",").rstrip(", ")
        related_people = related_person_form_data.rstrip(",").split(",")
        for related_person in related_people:
            related_permalink = slughifi(related_person)
            namesurname = related_person.split(" ")
            person_name = None
            person_surname = None
            if len(namesurname) != 1:
                person_surname = namesurname[-1]
                namesurname = namesurname[:-1]
                person_name = " ".join(namesurname)
            else:
                person_surname = namesurname[0]

            people = search_person( related_person )
            if people:
                names = ""
                for person in people:
                    person_permalink = slughifi(unicode(person))
                    if related_person != unicode(person):
                        names = names + ", " + unicode(person)
                        msg = string_concat(_('Person'), " '", unicode(related_person), "' ", _('is not present in the database!'), " ", _('Maybe you were looking for these people:'), names)
                        self._errors[related_person_str] = ErrorList([msg])
                    else:
                        related.append(person)
                        break
            else:
                msg = string_concat(_('Person is not present in the database:'), unicode(related_person))
                self._errors[related_person_str] = ErrorList([msg])
                
        logger.debug("Related: " + str(related))
        return related

def comma_split(s):
  out = ''
  lastc=''
  for c in s:
    if lastc=='\\':
      out+=c
    elif c==',':
      out = out.strip()
      if out:
        yield out
      out=''
    elif c!='\\':
      out+=c
    lastc = c
    
  out = out.strip()
  if out:
    yield out

def comma_escape(s):
  return s.replace('\\','\\\\').replace(',','\\,')
