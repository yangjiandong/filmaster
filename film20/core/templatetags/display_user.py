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
from django import template
from film20.config import *
from film20.core.models import RatingComparator
from django.conf import settings
from django.template import RequestContext
from film20.utils.cache_helper import *

DOMAIN = getattr(settings, 'DOMAIN', '')
FULL_DOMAIN = getattr(settings, 'FULL_DOMAIN', '')
LANGUAGE_CODE = settings.LANGUAGE_CODE

SUBDOMAIN_AUTHORS = getattr(settings, 'SUBDOMAIN_AUTHORS', False)

import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.inclusion_tag('filmasters/filmaster.html')
def display_user_with_similarity(logged_user, user):
    """Displays user's login, avatar and common taste with
       currently logged in user"""

    if logged_user.is_anonymous():
        score = None
    elif hasattr(user, 'score'):
        if user.score:
            score = user.score
        else:
            score = None
    else:
        try:
            score = RatingComparator.objects.get(main_user=logged_user,
                        compared_user=user).score
        except RatingComparator.DoesNotExist:
            score = None

    return {'user': user, 'score': score}

@register.inclusion_tag('user/user_and_rating.html')
def display_user_and_rating(user_and_rating):
    # link to profile    
    link = ""
    if SUBDOMAIN_AUTHORS:
        link += "http://" + unicode(user_and_rating.user.username) + '.'
        link += DOMAIN 
    else:
        link += '/' + str(urls.urls['SHOW_PROFILE'])
        link += '/'
        link += unicode(user_and_rating.user.username)

    user = unicode(user_and_rating.user)
    
    if user_and_rating.rating:
        rating = unicode(user_and_rating.rating.rating)
    else:
        reting = None

    # try to retrieve from cache
    short_review = get_cache(CACHE_SHORT_REVIEW_FOR_RATING, user_and_rating.rating.id)
    if short_review == None:
        # no, it doesn't ;)
        short_review = user_and_rating.rating.short_reviews.filter(LANG=LANGUAGE_CODE)[0:1]
        short_review = short_review and short_review[0] or False
        # store in cache (regardless if we found it or not)
        set_cache(CACHE_SHORT_REVIEW_FOR_RATING, user_and_rating.rating.id, short_review)

    short_review_text = short_review and unicode(short_review.review_text)

    return {            
       'link': link,
       'user': user,
       'score': user_and_rating.score,
       'rating': rating,
       'short_review': short_review,
       'short_review_text': short_review_text,
    }

def get_score_as_percent(score):

    score_prc = (10-score) * (10 - score)
    score_str = "%.1f" % score_prc
    return score_str

@register.inclusion_tag('filmasters/common_taste_indicator_string.html')
def display_users_common_taste(logged_user, compared_user):

    common_films = None
    if logged_user.is_anonymous():
        score = None
    else:
        try:
            comp = RatingComparator.objects.get(main_user=logged_user,
                        compared_user=compared_user)
            score = comp.score

        except RatingComparator.DoesNotExist:
            score = None

    if score:
        score_str = get_score_as_percent(score)
    else:
        score_str = None

    return {'score_str': score_str,
            'common_films': common_films,}

@register.inclusion_tag('filmasters/common_taste_indicator.html')
def score_as_percent(score, common_films=None):
    if score:
        score_str = get_score_as_percent(score)
        return {
            'score_str': score_str,
            'common_films': common_films,
        }
    else:
        return {'score_str': "?",
                'common_films': common_films,
                }

@register.inclusion_tag('user/common_taste_indicator.html')
def compare_users(user, comment_user, is_username=False):
    if user != comment_user:
        try:
            if is_username:
                key = "%s_%s" % (user.username, comment_user)
            else:
                key = "%s_%s" % (user.username, comment_user.username)
            rating = get_cache(CACHE_COMPARE_USERS, key)
            if rating is None:
                if is_username:
                    rating = RatingComparator.objects.get(main_user=user, compared_user__username=comment_user)
                else:
                    rating = RatingComparator.objects.get(main_user=user, compared_user=comment_user)
                set_cache(CACHE_COMPARE_USERS, key, rating)
            score_str = get_score_as_percent(rating.score)
            return {            
                'score_str': score_str,
                'common_films': rating.common_films,
            }
        except RatingComparator.DoesNotExist:
            return ""
    else:
        return ""

@register.simple_tag
def user_full_name(user):
    return user.get_full_name()

@register.simple_tag
def user_description(user):
    return user.get_profile().description

