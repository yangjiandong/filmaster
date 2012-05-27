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
#-*- coding: utf-8 -*-

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

tags = Tag.objects.all()

TAGS = {
            'Action':'Action',
            'Adventure':'Adventure',
            'Animation':'Animation',
            'Biography':'Biography',
            'Comedy':'Comedy',
            'Crime':'Crime',
            'Drama':'Drama',
            'Fantasy':'Fantasy',
            'Film-Noir':'Film-Noir',
            'History':'History',
            #'Horror':'Horror',
            'Music':'Music',
            #'Musical':'Musical',
            'Mystery':'Mystery',
            'Romance':'Romance',
            'Sci-Fi':'Sci-Fi',
            'Sport':'Sport',
            'Thriller':'Thriller',
            'War':'War',
            #'Western':'Western',
            'Short':'Short',
            'Sport':'Sport',
            'Independent':'Independent',
            'Family':'Family',
            'Documentary':'Documentary',
    }

def repair_tags():
    for tag in tags:
        if TAGS.has_key(unicode(tag)):
            tag.LANG = "en"
            tag.save()

if __name__ == "__main__":
    repair_tags()
