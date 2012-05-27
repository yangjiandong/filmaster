from django.db.models.query_utils import Q
from django import template
from django.db import models

from film20.regional_info.models import RegionalInfo
from film20.utils.slughifi import slughifi
from film20.utils.cache_helper import *
from film20.utils import cache

register = template.Library()


@register.inclusion_tag('widgets/regional_info.html', takes_context=True)
def regional_info(context):
    """
        Display local info
    """

    slug_city = None
    slug_region = None

    request = context['request']
    user = request.user
    if user.is_authenticated():
        profile = user.get_profile()
        try:
            slug_city = slughifi(profile.location)
        except AttributeError:
            slug_city = None
            

    if not slug_city:
        try:
            city = request.city
        except AttributeError:
            city = None

        slug_city = city and slughifi(city) or None
        
    key = cache.Key(CACHE_REGIONAL_INFO, slug_city)
    regional_info_obj = cache.get(key)

    if regional_info_obj is None and slug_city is not None:
        regional_info_obj = get_regional_info_obj(slug_city)
        cache.set(key, regional_info_obj)
        
    return {'regional_info': regional_info_obj,}


def get_regional_info_obj(city, region=""):
    """
        Returns regionl info object for
        give city and region
    """
    try:
        regional_info_obj = RegionalInfo.objects.get(Q(town__iexact=city) | Q(region=region))
    except:
        try:
            regional_info_obj = RegionalInfo.objects.get(town__iexact=city, region="")
        except:
            try:
                regional_info_obj = RegionalInfo.objects.get(region=region, town="")
            except:
                regional_info_obj = None
    return regional_info_obj

def clear_regional_info_cache(sender, instance, **kw):
    """
        If regional info object is saved clear regional_info cache
    """
    slug_city = slughifi(instance.town)
    slug_region = slughifi(instance.region)

    delete_cache(CACHE_REGIONAL_INFO,\
                    "%s_%s" % (slug_city, slug_region))


models.signals.pre_save.connect(clear_regional_info_cache, sender=RegionalInfo)
