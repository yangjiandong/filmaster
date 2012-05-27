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
from django.template import defaultfilters
import slughifi
import os, sys, getopt, glob
from settings import *
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings' 
import imdb, pickle
from film20.core.models import *
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from film20.tagging.models import Tag

import logging
logger = logging.getLogger(__name__)

people = Person.objects.all()

prefixes = {
        'ab':'ab',
        'Ab':'Ab',
        'abu':'abu',
        'Abu':'Abu',
        'bin':'bin',
        'Bin':'Bin',
        'bint':'bint',
        'Bint':'Bint',
        'da':'da',
        'Da':'Da',
        'de':'de',
        'De':'De',
        'degli':'degli',
        'Degli':'Degli',
        'della':'della',
        'Della':'Della',
        'der':'der',        
        'Der':'Der',
        'di':'di',
        'Di':'Di',
        'del':'del',
        'Del':'Del',
        'dos':'dos',
        'Dos':'Dos',
        'du':'du',
        'Du':'Du',
        'el':'el',
        'El':'El',
        'fitz':'fitz',
        'Fitz':'Fitz',
        'haj':'haj',
        'Haj':'Haj',
        'hadj':'hadj',
        'Hadj':'Hadj',
        'hajj':'hajj',
        'Hajj':'Hajj',
        'ibn':'ibn',
        'Ibn':'Ibn',
        'ter':'ter',
        'Ter':'Ter',
        'tre':'tre',
        'Tre':'Tre',
        'van':'van',
        'Van':'Van',
        'Von':'Von',
        'von':'von',
        }

def repair_surnames():
    for person in people:
        index = None
        sPerson = unicode(person)
        list = sPerson.split(' ')
        if len(list)> 2:
            for index, element in enumerate(list):
                if prefixes.has_key(element):
                    name = " ".join(list[:index])
                    surname = " ".join(list[index:])
                    person.name = name
                    person.surname = surname
                    person.save(saved_by=2)
                    break
                else:
                    pass

            if list[-1] == "Jr.":  
                name = " ".join(list[:-2])
                surname = " ".join(list[-2:])
                person.name = name
                person.surname = surname
                person.save(saved_by=2)

if __name__ == "__main__":
    repair_surnames()
