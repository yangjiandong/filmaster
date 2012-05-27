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
from django.utils.translation import gettext_lazy as _
from django.db import models
from django.contrib import admin
from datetime import datetime

from django.contrib.auth.models import User

from film20.utils.cache_helper import *
from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE

import logging
logger = logging.getLogger(__name__)

# Create your models here.
class RegionalInfoManager(models.Manager):
    
    # overridden method for FLM-707
    def get_query_set(self):
        return super(UserActivityManager, self).get_query_set().filter(
            LANG=LANGUAGE_CODE)   
        
class RegionalInfo(models.Model):
    
    user = models.ForeignKey(User, related_name="regional_info_editor")
    town = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    contents = models.TextField(null=True, blank=True)
    
    #timestamp    
    modified_at = models.DateTimeField(_("Modified at"),default=datetime.now)
    created_at = models.DateTimeField(_("Created at"),default=datetime.now)
    
    #LANG
    LANG = models.CharField(max_length=2, default=LANGUAGE_CODE)
    
    def save(self):
        from film20.utils.slughifi import slughifi
        if self.town=="":
            slug_town = None
        else:
            slug_town = slughifi(self.town)
        if self.region=="":
            slug_region = None
        else:
            slug_region = slughifi(self.region)
        delete_cache(CACHE_REGIONAL_INFO, "%s_%s" % (slug_town, slug_region))
        super(RegionalInfo, self).save()

    def delete(self):
        from film20.utils.slughifi import slughifi
        if self.town=="":
            slug_town = None
        else:
            slug_town = slughifi(self.town)
        if self.region=="":
            slug_region = None
        else:
            slug_region = slughifi(self.region)
        delete_cache(CACHE_REGIONAL_INFO, "%s_%s" % (slug_town, slug_region))
        super(RegionalInfo, self).delete()

    def __unicode__(self):
        return '%s, %s' % (self.town, self.region)
