from django import template
from django.contrib.flatpages.models import FlatPage
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from film20.utils.cache_helper import *
from film20.utils import cache

FLATPAGE_FILMASTER_RECOMMENDS = getattr(settings, 'FLATPAGE_FILMASTER_RECOMMENDS', 'filmaster-recommends')

register = template.Library()


@register.inclusion_tag('widgets/recommended_users.html', takes_context=True)
def recommended_users(context):
    """
        Widget displays list of recommended users to follow.
    """

    RECOMMENDED_USERS = getattr(settings, 'RECOMMENDED_USERS')
    users = [User.objects.get(username__iexact=user) for user in \
                RECOMMENDED_USERS]

    return {'users': users,
            'loggeduser': context['request'].user}


@register.inclusion_tag('widgets/filmaster_recommends.html')
def filmaster_recommends():
    """
        A widget displaying HTML from a selected flat page.
        Define this page in settings.py to FLATPAGE_FILMASTER_RECOMMENDS
    """
    key = cache.Key(FLATPAGE_FILMASTER_RECOMMENDS)

    flat_page = cache.get(key)

    if flat_page is None:
        try:
            flat_page = FlatPage.objects.get(url=FLATPAGE_FILMASTER_RECOMMENDS)
        except FlatPage.DoesNotExist:
            flat_page = False
        cache.set(key, flat_page, cache.A_DAY)

    return {'flat_page': flat_page}


def clear_filmaster_recommends_cache(sender, instance, **kw):
    """
        If flat page is saved clear filmaster_recommends cache
    """
    if instance.url == FLATPAGE_FILMASTER_RECOMMENDS:
        key = cache.Key(FLATPAGE_FILMASTER_RECOMMENDS)
        cache.delete(key)


models.signals.pre_save.connect(clear_filmaster_recommends_cache, sender=FlatPage)
