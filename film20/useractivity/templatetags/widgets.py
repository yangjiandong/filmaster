import random
from datetime import datetime, timedelta

from django import template
from django.conf import settings

from film20.useractivity.models import UserActivity
from film20.useractivity.useractivity_helper import UserActivityHelper
from film20.utils.cache_helper import *
from film20.recommendations.recom_helper import RecomHelper
from film20.config.urls import urls
from film20.utils import cache

register = template.Library()

@register.inclusion_tag('widgets/latest_checkins.html')
def latest_checkins():
    """
        Widget for main page (for unregistered users) displaying X
        random check-ins by Filmaster users.
    """
    key = cache.Key("latest-checkins")
    latest = cache.get(key)

    NUMBER_OF_LATEST_CHECKINS = getattr(settings,
            'NUMBER_OF_LATEST_CHECKINS', 10)
    NUMBER_OF_CHECKINS_AT_MAIN_PAGE = getattr(settings,
            'NUMBER_OF_CHECKINS_AT_MAIN_PAGE', 4)

    if not latest:

        now = datetime.now()
        ago = now - timedelta(hours=3)
        checkins = UserActivity.objects.all_checkins().order_by('-created_at')

        latest = list(checkins.filter(created_at__gte=ago)[:NUMBER_OF_LATEST_CHECKINS])
        if len(latest) < NUMBER_OF_CHECKINS_AT_MAIN_PAGE:
            latest = list(checkins)[:NUMBER_OF_LATEST_CHECKINS]

        cache.set(key, latest, cache.CACHE_HOUR * 3)

    try:
        latest = random.sample(latest, NUMBER_OF_CHECKINS_AT_MAIN_PAGE)
    except ValueError:
        latest = latest[:NUMBER_OF_CHECKINS_AT_MAIN_PAGE]

    return {'activities': latest, }

@register.inclusion_tag('widgets/latest_ratings.html')
def latest_ratings():
    """
        Widget for main page (for unregistered users)
        displaying X random ratings by Filmaster users.
    """

    key = cache.Key("latest_ratings")
    ratings = cache.get(key)

    NUMBER_OF_LATEST_RATINGS = getattr(settings,
            'NUMBER_OF_LATEST_RATINGS', 10)
    NUMBER_OF_RATINGS_AT_MAIN_PAGE = getattr(settings,
            'NUMBER_OF_RATINGS_AT_MAIN_PAGE', 4)

    if not ratings:
        ratings = UserActivity.objects.all_ratings().\
                order_by('-created_at')[:NUMBER_OF_LATEST_RATINGS]
        cache.set(key, ratings, cache.A_DAY)

    try:
        ratings = random.sample(ratings, NUMBER_OF_RATINGS_AT_MAIN_PAGE)
    except ValueError:
        ratings = ratings[:NUMBER_OF_RATINGS_AT_MAIN_PAGE]

    return {'activities': ratings, }

@register.inclusion_tag('home/show_activities.html', takes_context=True)
def main_page_activity_list(context):
    """
        Widget for main page (for not logged in users)
        Displays list of recent activities on Filmaster.
    """

    key = cache.Key("main_page_activities_displayed")

    displayed_activities = cache.get(key)
    if not displayed_activities:
        uahelper = UserActivityHelper()
        displayed_activities = uahelper.main_page_featured_activities()
        cache.set(key, displayed_activities, cache.CACHE_HOUR)

    return {'activities': displayed_activities,
            'request': context.get('request'),
           }


