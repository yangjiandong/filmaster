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
from django.shortcuts import render_to_response
from film20.config.urls import templates
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.views.decorators.cache import never_cache

from film20.regional_info.models import RegionalInfo

from film20.utils.cache_helper import *
from film20.utils.utils import json_return

import logging
logger = logging.getLogger(__name__)

# Create your views here.
@never_cache
def regional_info(request):
    city = None
    try:
        city = request.city
    except AttributeError:
        city = None
    region = None
    try:
        region = request.region
    except AttributeError:
        region = None

    logger.debug("Getting regional info for %s, %s" % (city, region))
    return regional_info_args(request, city, region)

@never_cache
def regional_info_args(request, town, region):
	
    from film20.utils.slughifi import slughifi
    if town is not None:
        slug_town = slughifi(town)
    else: 
        slug_town = None
    if region is not None:
        slug_region = slughifi(region)
    else: 
        slug_region = None

    # try to retrieve from cache
    regional_info_contents = get_cache(CACHE_REGIONAL_INFO, "%s_%s" % (slug_town, slug_region))
#    regional_info_contents = None

    if regional_info_contents == None:
        regional_info_object = None
        try:    
            regional_info_object = RegionalInfo.objects.get(Q(town=town) | Q(region=region))
        except:
            try:
                logger.info("No regional info for town %s and region %s" % ( town, region ))
                regional_info_object = RegionalInfo.objects.get(town=town, region="")
            except:
                try:
                    logger.info("No regional info for town %s" % ( town ))
                    regional_info_object = RegionalInfo.objects.get(region=region, town="")
                except:
                    logger.info("No regional info for region %s" % ( region ))
 
        if regional_info_object == None:
            regional_info_contents = "NONE"
        else:
            regional_info_contents = regional_info_object.contents
 
        # store in cache
        set_cache(CACHE_REGIONAL_INFO, "%s_%s" % (slug_town, slug_region), regional_info_contents)
        
    data = {
            'town': town,
            'region': region,
            'contents': regional_info_contents,
        }
    
    return json_return(data)
