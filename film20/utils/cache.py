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

try:
    # django 1.3 and higher
    from django.core.cache import cache
except ImportError:
    # django 1.2
    from django.utils.cache import cache
from django.db.models.query import QuerySet

import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User

CACHE_MIDDLEWARE_KEY_PREFIX = getattr(settings, 'CACHE_MIDDLEWARE_KEY_PREFIX', 'filmaster')

# time periods
A_QUARTER = 60*15
AN_HOUR = 3600
A_DAY = 60*60*24
A_WEEK = A_DAY*7
A_MONTH = A_DAY*30

# default cache time is 24 hours
DEFAULT_CACHE_TIME = A_DAY
CACHE_FIVE_MINUTES = 60 * 5
CACHE_HOUR = 60 * 60
CACHE_HALF_HOUR = 60 * 30


# cache constants for films_to_rate engine (fast and clever way to suggest
# movies to rate to user
CACHE_USER_BASKET = "cache_user_basket"
CACHE_SPECIAL_USER_BASKET = "cache_special_user_basket"
CACHE_TAG_BASKET = "cache_tag_basket"

# cache constants for users
CACHE_RECOMMENDED_FILMS_HOME_PAGE = "recommended_films_home_page" # template: recommended_films_home_page_USERID
CACHE_OTHERS_RATINGS = "others_ratings" # template: others_ratings_OBJECTID_USERID
CACHE_USER_RATINGS_COUNT = "user_ratings_count" # template: user_ratings_count_USERID

# sitemaps
CACHE_SITEMAP_SHORT_REVIEWS = "sitemap_short_reviews"

# general cache constants
CACHE_FILM = "film" # template: film_PERMALINK, e.g. film_wiedzmin 
CACHE_FILM_DIRECTORS = "film_directors" # template: film_directors_PERMALINK, e.g. film_directors_wiedzmin
CACHE_FILM_ACTORS = "film_actors" # template: film_actors_PERMALINK, e.g. film_actors_wiedzmin
CACHE_RELATED_FILMS = "related_films" # template: related_films_FILMID
CACHE_PERSON_LOCALIZED = "person_localized_v2" # template: person_localized_PERSONID
CACHE_TAGS_FOR_OBJECT_LOCALIZED = "tags_for_object_localized" # template: tags_for_object_OBJECTID
CACHE_AVATAR = "avatar_url" # template: avatar_url_USERNAME_SIZE, e.g. avatar_url_michuk_72
CACHE_SHORT_REVIEW_FOR_RATING = "short_review_for_rating_v2" # template: short_review_for_rating_RATINGID
CACHE_SHOP_ITEM_FOR_FILM = "shop_item_for_film"  # template: shop_item_for_film_FILMID

# contest
CACHE_VOTES_FOR_CHARACTER_IN_GAME = "votes_for_character_in_game" # template votes_for_character_in_game_GAMEID_CHARACTERID

# regional
CACHE_REGIONAL_INFO = "regional_info" # template: regional_info_town_region

# special object meaning 'None' - for caching purposes
CACHE_OBJECT_NONE = "I'm an dead parrot code-named $d,SsserrrrDDD. I was alive when they bought me. I promise."

# planet
CACHE_PLANET = "cache_planet" # template: cache_planet_KEY

# django digg
CACHE_VOTE = "cache_vote" # template: cache_vote_username_KEY

# threadedcomments
CACHE_COMMENTS = "cache_comments" # template: cache_comments_KEY

# compare_users
CACHE_COMPARE_USERS = "cache_compare_users" # template: cache_compare_users_USERNAME1_USERNAME2

# followers
CACHE_FOLLOWERS = "cache_followers" # template: cache_followers_USERNAME_STATUS

# activities
CACHE_ACTIVITIES = "cache_activities"

# filmaster recommends block
CACHE_FILMASTER_RECOMMENDS = "cache_filmaster_recommends"

# latest ratings
CACHE_LATEST_RATINGS = "cache_latest_ratings"

# popular films
CACHE_POPULAR_FILMS = "cache_popular_films"

# user features
CACHE_USER_FEATURES = "cache_user_features"

# film features
CACHE_FILM_FEATURES = "cache_film_features"

# item features
CACHE_ITEM_FEATURES = "cache_item_features"

# map cache strings here if caching time is not default (24 hours) 
CACHE_TIMEOUTS  = {
    CACHE_FILM: A_WEEK,
    CACHE_SHOP_ITEM_FOR_FILM: A_WEEK,
    CACHE_FILM_DIRECTORS: A_MONTH,
    CACHE_FILM_ACTORS: A_MONTH,
    CACHE_RELATED_FILMS: A_WEEK,
    CACHE_PERSON_LOCALIZED: A_MONTH,
    CACHE_SHORT_REVIEW_FOR_RATING: A_MONTH,
    CACHE_USER_FEATURES: A_MONTH,
    CACHE_FILM_FEATURES: A_MONTH,
}

# keys for caching recent reviews and featured review on MOVIES page.
KEY_RECENT = 'recent_reviews'
KEY_FEATURED = 'featured_review'

from django.db import models
from django.utils.encoding import smart_str
import hashlib

# class for safe key generation
# makes valid cache key from everything

class Key(object):
    
    class _default_opts:
        timeout = None
        is_common = False
        version = None

    def __init__(self, prefix, *args):
        self.prefix = self._fmt_key(prefix)
        self.opt = settings.CACHE_PREFIXES.get(prefix, self._default_opts)
        
        if not self.opt.is_common:
            self.key = CACHE_MIDDLEWARE_KEY_PREFIX + self.prefix
        else:
            self.key = "common_" + self.prefix

        if args:
            self.key += "_" + self._fmt_key(*args)
        if self.opt.version:
            self.key += "_v%s" % self.opt.version
            
        if len(self.key)>230:
            self.key = "%s_%s" % (self.prefix, hashlib.md5(self.key).hexdigest())
        else:
            # replace control chars by underscores
            self.key = ''.join((c > ' ' and c or '_') for c in self.key)
    
    def __str__(self):
        return self.key

    def __repr__(self):
        return "Key: %s" % self.key

    @classmethod
    def _fmt_key(cls, *args):
        if len(args) == 0:
            return ""
        if len(args) > 1:
            return "_".join(cls._fmt_key(arg) for arg in args)
        arg = args[0]
        if isinstance(arg, QuerySet):
            return '(%s)' % cls._fmt_key(*list(arg))
        if isinstance(arg, (list, tuple)):
            return '(%s)' % cls._fmt_key(*arg)
        if isinstance(arg, (User, AnonymousUser)):
            return arg.username or 'Anonymous-User'
        if isinstance(arg, models.Model):
            return smart_str(arg.pk)
        if isinstance(arg, (int, long)):
            return str(arg)
        if isinstance(arg, dict):
            return cls._fmt_key(*sorted(arg.items(), key=lambda i:i[0]))
        import datetime
        if isinstance(arg, datetime.datetime):
            return arg.strftime("%Y%m%d%H%M%S")
        if isinstance(arg, datetime.date):
            return arg.strftime("%Y%m%d")
        return smart_str(arg)

    @property
    def timeout(self):
        return self.opt.timeout or CACHE_TIMEOUTS.get(self.prefix) or DEFAULT_CACHE_TIME

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return str(self) == other

from film20.middleware.threadlocals import get_request

def get(key):
    if settings.CAN_SKIP_CACHE:
        request = get_request()
        if request and 'nocache' in request.GET \
                and request.user.has_perm('can_skip_cache'):
            logger.debug("FORCED MISS: %s", key)
            return None
    ret = cache.get(str(key))
    if ret is None:
        logger.debug("MISS: %s", key)
    else:
        logger.debug("HIT: %s", key)
    return ret

def get_many(keys):
    if settings.CAN_SKIP_CACHE:
        request = get_request()
        if request and 'nocache' in request.GET \
                and request.user.has_perm('can_skip_cache'):
            logger.debug("FORCED MISS: %s", key)
            return [None] * len(keys)
    return cache.get_many([str(key) for key in keys])

def set(key, value, time=None):
    if not time:
        time = isinstance(key, Key) and key.timeout or DEFAULT_CACHE_TIME
    try:
        cache.set(str(key), value, time)
        logger.debug("set: %s, timeout: %s", key, time)
    except Exception, e:
        logger.exception(e)
        delete(key)

def incr(key):
    return cache.incr(str(key))

def delete(key):
    cache.delete(str(key))
    logger.debug("delete: %s", key)

def set_cache(prefix, key, value, time=None):
    set(Key(prefix, key), value, time)

def get_cache(prefix, key):
    return get(Key(prefix, key))

def delete_cache(prefix, key):
    return delete(Key(prefix, key))

def clear():
    cache.clear()

def cache_query(query, prefix, *args):
    key = Key(prefix, *args)
    result = get(key)
    if result is None:
        result = list(query)
        set(key, result)
    return result

