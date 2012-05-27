#! -!- coding: utf-8 -!-
import os, sys
sys.setrecursionlimit(100000)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
def ABS_DIR(rel):
  return os.path.join(BASE_DIR, rel.replace('/',os.path.sep))

# import film20.utils.log.setup

ADMINS = (
     ('Filmaster', 'filmaster@filmaster.com'),
     ('Mariusz Krynski', 'mrk@sed.pl'),
)

MANAGERS = ADMINS

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15

# For English version:
LANGUAGE_CODE = 'en'
COUNTRY = 'United States'
COUNTRY_CODE = 'US'
LANGUAGES = (
  ('en', 'English'),
)
# English time format
SCREENING_TIME_FORMAT = "l, j E, f a"
# Polish time format
#SCREENING_TIME_FORMAT = "l, j E, H:i"

COUNTRIES_WITH_SHOWTIMES = ('PL', 'GB', 'US', )

COUNTRY_MAIN_CITY = {
        "PL": {'name': "Warszawa", "latitude": "52.23", "longitude": "21.01"},
        "US": {'name': "New York", "latitude": "40.71", "longitude": "-74"},
        "GB": {"name": "London", "latitude": "51.5", "longitude": "-0.13"},
}

FBAPP = dict(
    config=dict(
        no_of_movies=500,
        no_of_directors=50,
        no_of_actors=50,
        movies_to_rate_on_page=3,
        movies_to_rate_for_progress=6,
        no_of_questions=10,
        movie_years=3,
    ),
    points=dict(
        rated_movie=10,
        film_selected=10,
        invited_friend=5,
        wallpost=20,
        seconds={
            1:10,
            2:10,
            3:10,
            4:9,
            5:8,
            6:7,
            7:6,
            8:5,
            9:4,
            10:3,
            11:2,
            12:2,
            13:1,
            14:1,
            15:2,
        },
    )
)

DISTANCE_THRESHOLD = 30

# For English version
LOGIN_URL = "/account/login/"
LOGOUT_URL = "/account/logout/"

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'OPTIONS': {
            'MAX_ENTRIES': 2**30,
        },
        'VERSION': 1,
    }
}

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True
CACHE_SITEMAP_HOURS = 24 * 7
CACHE_SITEMAP_SUBDOMAIN_HOURS = 24

INSTALLED_APPS = (
    'grappelli',
    'filebrowser',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.flatpages',
    'django.contrib.admin',
    'django.contrib.markup',
    'django.contrib.sitemaps',
    'film20.messages', # must be before django.contrib.messages (for testing)
    'django.contrib.messages',
    # external
    'haystack',

    'django_openidauth',
    'django_openidconsumer',

    'ajax_validation',
    'gravatar',
    'compressor',
    'compress',
    'piston',

    'south',

    'film20.notification',

    'film20.core',
    'film20.showtimes',
    'film20.contest',
    'film20.facebook_connect',
    
    'film20.fbapp',
    'film20.account',
    'film20.userprofile',
    'film20.tagging',
    'film20.config',
    'film20.blog',
    'film20.threadedcomments',
    'film20.externallink',
    
    'film20.demots',
    
    'film20.useractivity',    
    
    'film20.filmbasket',
    'film20.event',
    'film20.festivals',
    
    'film20.legacy_redirects',
    'film20.shop',
    'film20.followers',
    'film20.import_ratings',
    'film20.recommendations',
    'film20.import_films',
    
    
#    'film20.geo',
    
#    'film20.regional_info',
    'film20.search',
    'film20.add_films',
    'film20.massemail',

    'film20.emailconfirmation',
    'film20.pagination',
    'film20.oembed',

    'film20.api',
    'film20.forum', #TODO delete after applying migration scripts for permalinks

    'film20.usersubdomain',
    'film20.posters',
    
    'film20.register',
    'film20.pingback',
    'djcelery',
    'film20.dashboard',
    'film20.publicprofile',
    'film20.regional_info',
    'film20.usersettings',
    'film20.fragment',
    'film20.upload',
    'film20.moderation',
    'film20.merging_tools',
    'film20.badges',
    
    'film20.film_features',
    'film20.vue',
#    'google_fetcher',
)

AN_HOUR = 3600
A_QUARTER = 900
A_DAY = 3600 * 24
A_MONTH = 30 * A_DAY
A_YEAR = 365 * A_DAY

class opt:
    def __init__(self, timeout, version=None, is_common=False):
        self.timeout = timeout
        self.version = version
        self.is_common = is_common

CACHE_PREFIXES = {
    "user_profile": opt(A_DAY, version=1, is_common=True),
    "tv_user_recommended": opt(AN_HOUR, version=2),
    "cinema_user_recommended": opt(AN_HOUR, version=2),
    "top_personalized_recommendations": opt(AN_HOUR),
    "sitemap_paginator": opt(A_DAY),
    "tagged_films": opt(AN_HOUR),
    "open_festivals": opt(A_MONTH),
    "festival_screening_dates": opt(A_MONTH, version=1),
    "festival_participants": opt(AN_HOUR, version=3),
    "festival_screenings": opt(A_MONTH, version=1),
    "festival_theaters": opt(A_MONTH, version=2),
    "festival_films": opt(A_MONTH, version=1),
    "festival_screening_set": opt(A_MONTH, version=3),
    "country_tz": opt(AN_HOUR),
    "film_top_directors": opt(A_MONTH),
    "film_actors": opt(A_MONTH),
    "film_featured_posts": opt(A_DAY),
    "film_related_films": opt(A_DAY),
    "film_friends_ratings": opt(A_DAY),
    "film_similar_ratings": opt(A_DAY),
    "film_videos": opt(A_DAY),
    "anonymous_wall": opt(A_QUARTER),
    "user_recommendations": opt(A_DAY, version=1),
    "user_channels": opt(A_DAY, is_common=True),
    "town_channels": opt(A_DAY, is_common=True),
    "town_cinemas": opt(A_DAY, is_common=True),
    "country_cinemas": opt(A_DAY, is_common=True),
    "country_towns": opt(A_DAY, is_common=True, version=1),
    "country_tv": opt(A_DAY, is_common=True),
    "checkins": opt(A_DAY),
    "showtime_dates": opt(A_DAY),
    "showtimes_town_films": opt(AN_HOUR * 4, version=2),
    "showtimes_country_tv_films": opt(AN_HOUR * 4, version=3),
    "channels_films": opt(A_DAY),
    "film_on_channel": opt(A_DAY),
    "film_screenings": opt(A_DAY),
    "channel_screenings": opt(A_DAY),
    "tvchannel_default": opt(A_DAY),
    "user_ratings": opt(A_DAY, is_common=True),
    "recently_seen_film_ids": opt(A_DAY, is_common=True),
    "long_ago_seen_film_ids": opt(A_DAY, is_common=True),
    "user_basket": opt(A_DAY, is_common=True),
    "film_rankings": opt(A_DAY),
    "popular_films_list": opt(A_DAY),
    "main_page_activities_all": opt(A_DAY),
    "main_page_activities_displayed": opt(AN_HOUR),
    "twitter_activity": opt(AN_HOUR),
    "filmlocalized_cached_query": opt(A_DAY),
    "objectlocalized_cached_query": opt(A_DAY),
    "profile_page_best_films": opt(A_QUARTER),
    "geolocation": opt(AN_HOUR, is_common=True),
    "conversation_unread_counter": opt(A_MONTH, is_common=True),
    "cache_film_features": opt(A_YEAR, is_common=True),
    "cache_user_features": opt(A_YEAR, is_common=True),
    "cache_item_features": opt(A_YEAR, is_common=True),
    "vue_rater_user_films": opt(A_YEAR, version=2),
    "related_films": opt(A_DAY, version=2),
}

SHOWTIMES_EMPTY_CACHE_TIMEOUT = AN_HOUR

NOTICE_MEDIA = (
    'film20.notification.media.EMail',
#    'film20.notification.media.Jabber',
    'film20.notification.media.Facebook',
    'film20.notification.media.Twitter',
    'film20.notification.apns.iPhonePush',
)

NOTIFICATION_QUEUE_ALL = True
NOTIFICATION_LANGUAGE_MODULE = 'core.profile'
NOTIFICATION_FORCE_SITE_LANG = False

SMS_PROVIDER_USERNAME = None
SMS_PROVIDER_PASSOWRD = None

AUTHENTICATION_BACKENDS = (
    "film20.account.email_backend.EmailLoginBackend",
    "film20.account.email_backend.CaseInsensitiveLoginBackend",
    "film20.account.backends.TwitterAuthBackend",
    "film20.account.backends.FourSquareAuthBackend",
    "film20.facebook_connect.facebookAuth.FacebookBackend",
    "django.contrib.auth.backends.ModelBackend",
)

MIDDLEWARE_CLASSES = (
#    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware', #cache
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'film20.core.middleware.PostCommitMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django_openidconsumer.middleware.OpenIDMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.doc.XViewMiddleware',
#    'djangologging.middleware.LoggingMiddleware',
    'film20.core.middleware.ForceSSLLogin',
    'film20.core.middleware.ClientPlatform',
    'film20.middleware.threadlocals.ThreadLocals',
    'film20.pagination.middleware.PaginationMiddleware',
    'film20.core.middleware.CoreMiddleware',
    'film20.facebook_connect.facebookMiddleware.fbMiddleware',
    'film20.usersubdomain.middleware.UserSubdomainMiddleware',
    'film20.geo.middleware.GeoMiddleware',
#    'film20.core.middleware.BetaMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware', #cache
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'film20.core.context_processors.settings',
    'film20.core.context_processors.msg',
    'film20.core.context_processors.auth',
    'film20.core.context_processors.global_context',
#    'film20.geo.context.geo_context',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    ABS_DIR("new_templates"),
    ABS_DIR("django_openidauth/templates"),
    ABS_DIR("../compress/templates"),
)

DIRECTORY_URLS = (
    'http://blogsearch.google.com/ping/RPC2',
    'http://ping.feedburner.com',
    'http://ping.syndic8.com/xmlrpc.php',
    'http://rpc.icerocket.com:10080/',
    'http://rpc.weblogs.com/RPC2',
)

ROOT_URLCONF = 'film20.urls'

AUTH_PROFILE_MODULE = "core.profile"

MESSAGE_STORAGE = 'film20.utils.messages.CookieUniqueStorage'

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
# ALL INSTANCES SHARING THE SAME DATABASE MUST USE THE SAME TIME_ZONE !
TIME_ZONE = 'Europe/Warsaw'

#defines whether we should user subdomains like nick.filmaster.pl
SUBDOMAIN_AUTHORS = False

ANALYTICS_CODE = 'NONE'
FLAKER_LINK = ''
FACEBOOK_URL = 'http://www.facebook.com/FilmasterCom'
TWITTER_URL = 'http://twitter.com/#!/Filmaster'
DEFAULT_FETCHER = 'rottentomatoes'

COMPRESS = True
COMPRESS_VERSION = True

COMPRESS_CSS = {
    'my_screen_css': {
        'source_filenames': ('style.css', 'jquery.autocomplete.css'),
        'output_filename': 'one_compressed.css',
        'extra_context': {
            'media': 'screen,projection',
        },
    },
}

COMPRESS_JS = {
    'my_scripts': {
        'source_filenames': ('js/jquery-1.4.2.min.js', 'js/jquery.form-2.11.js', 'js/contest/jquery.tools.min.js', 'js/jquery.textareacount.js', 'js/jquery.autocomplete.min.js', 'js/jquery.tooltip.js', 'js/jquery.bgiframe.js', 'js/jquery.dimensions.js', 'js/jquery.autogrow.js', 'js/comments.js', 'js/utils.js','js/easySlider.packed.js','js/planet.js','js/jquery-ui-1.8.5.custom.min.js',),
        'output_filename': 'js/all_compressed.js',
    }
}

COMPRESS_JS_FILTERS = [
    'compressor.filters.yui.YUIJSFilter',
]
COMPRESS_YUI_BINARY = ABS_DIR( 'yuicompressor-2.4.7.jar' )

# alg1 - old algorithm described here: http://filmaster.org/display/DEV/Recommendations+engine
# alg2 - new algorithm described here: http://filmaster.org/display/DEV/New+recommendation+engine#Newrecommendationengine-SecondapproachpresentlyusedonFilmasterasguessalgorithm2basedonideasdevelopedbytheteamsparticipatinginNetflixCompetition
RECOMMENDATION_ALGORITHM = "alg2"

# alg1 - old algorithm based on tags
# alg2 - new algorithm based on Jakub Talka work described here: http://filmaster.org/display/DEV/Similar+films
SIMILAR_FILMS_ALGORITHM = "alg2"

## LITERALS ##
NUMBER_OF_RECOMMENDED_FILMS_FRONT_PAGE = 3
NUMBER_OF_COMMENTS_FRONT_PAGE = 5
NUMBER_OF_REVIEWS_FRONT_PAGE = 12
NUMBER_OF_REVIEWS_TAG_PAGE = 6
NUMBER_OF_MOVIES_WISHLIST_SIDEBAR = 6
NUMBER_OF_MOVIES_SHITLIST_SIDEBAR = 4

NUMBER_OF_MOVIES_FOR_WIDGET = 4

# Rating process
RATE_BASKET_SIZE = 24 # how many movies to rate we store in cache for user
MIN_RATE_BASKET_SIZE = 12 # how many movies to rate we store in cache for user
TAG_BASKET_SIZE = 70 # how many movies we store in genre basket
MIN_TAG_BASKET_SIZE = 20 # indicates when we have to refill genre basket
MIN_RATE_BASKET_SIZE = 15 # indicates when we have to refill basket

# how many movies at most we can keep in special basket
SPECIAL_RATE_BASKET_SIZE = 6
# which tag baskets we use to refill standard user basket
BASKETS_TAGS_LIST = ['dramat', 'animowany', 'horror', 'komedia',
        'przygodowy', 'fantastyczny', 'science-fiction', 'sensacyjny',
        'romans', 'western', 'wojenny']

NEW_RATING_SYSTEM = True

# how many movies are added to special basket with rated film
SPECIAL_BASKET_BONUS = 4
# what should be the rate at least to update special basket by film
MIN_RATE_FOR_SPECIAL_BASKET = 7

# Top personalized recommendations
PERSONALIZED_CINEMA_DAYS = 2
PERSONALIZED_TV_DAYS = 2
PERSONALIZED_CINEMA_FILMS_NUMBER = 3
PERSONALIZED_TV_FILMS_NUMBER = 3

NUMBER_OF_FILMS_RELATED = 6

RECOMMENDATIONS_MIN_VOTES_USER = 15 # how many movies the user has to rate to get first recommendations
RECOMMENDATIONS_MIN_VOTES_FILM = 15 # how many rates, movie has to have, to be considered for recommendations

RANKING_MIN_NUM_VOTES_FILM = 75
RANKING_MIN_NUM_VOTES_OTHER = 25

RATING_BASKET_SIZE = 100
RATING_TAG_BASKET_SIZE = 20
RATING_SEEN_DAYS = 30

SIMILAR_USER_LEVEL = 2

TOP_TAGS_NUMBER = 20
RATING_FILMS_NUMBER = 6

USER_RATINGS_NOTICE_IDLE_SECONDS = 1800
USERACTIVITY_GROUPING_PERIOD = 1800 # time between the first and last activity in group
RECOMPUTE_USER_FEATURES_TIME_OFFSET = 3 * 60 # time between first rating and recompute_user_features call

MIN_COMMON_FILMS = 5 # for recommendations (alg 1)
MIN_COMMON_TASTE = 2.1 # for recommendations (alg 1)

MIN_FILM_COMPARATOR_SCORE = 0.2 # for film comparator

NUMBER_OF_OTHERS_RATINGS = 5
NUMBER_OF_FRIENDS_RATINGS = 5
NUMBER_OF_ITEMS_PUBLIC_PROFILE= 5
NUMBER_OF_ACTIVITIES = 20
MAX_RELATED_ARTICLES = 5
NUMBER_OF_SIMILAR_USERS_ON_PAGE = 20
NUMBER_OF_SIMILAR_USERS_PAGES = 10
NUMBER_OF_SIMILAR_USERS_ON_TAG = 4

NUMBER_OF_MESSAGES = 20

WEEKLY_RECOMMENDATIONS_NUMBER_OF_FILMS = 4
WEEKLY_RECOMMENDATIONS_MAX_NUMBER_OF_FILMS = 15

MIN_CHARACTERS_COMMENT_APPLY = False # whether to apply the constraint for minimal number of characters for comments
MIN_CHARACTERS_COMMENT = 10 # minimal number of characters for a comment
DUPLICATE_COMMENT_MINUTES = 5 # number of minutes after which identical comment is not considered duplicate anymore

MIN_CHARACTERS_SHORT_REVIEW = 10
MAX_CHARACTERS_SHORT_REVIEW = 1000

MAX_EXTERNAL_LINKS = 5

FAST_RECOMMENDATIONS_NUMBER_OF_TOP_FILMS = 200

# movie page

MAX_NUMBER_OF_SCREENINGS = 6

# main page for not logged user

POPULAR_FILMS_MAIN_PAGE_NUMBER = 4
CINEMA_FILMS_MAIN_PAGE_NUMBER = 4
TV_FILMS_MAIN_PAGE_NUMBER = 4
POPULAR_FILMS_MAIN_PAGE_NUMBER_ALL = 30
MAIN_PAGE_FILMS_IN_ROW_NUMBER = 4
TWEETS_DISPLAYED_NUMBER = 2
NUMBER_OF_LATEST_RATINGS = 10
NUMBER_OF_RATINGS_AT_MAIN_PAGE = 4
NUMBER_OF_LATEST_CHECKINS = 10
NUMBER_OF_CHECKINS_AT_MAIN_PAGE = 4
FILMS_IN_CINEMAS_DAYS_AHEAD = 3

MAIN_PAGE_TYPES_OF_ACTIVITIES = {
    'TYPE_POST': 3,
    'TYPE_SHORT_REVIEW': 3,
    'TYPE_COMMENT': 2,
    'TYPE_RATING': 2,
    'TYPE_LINK': 0,
    'TYPE_FOLLOW': 0,
    'TYPE_CHECKIN': 2,
}

# film page
MAX_ACTORS = 15 # number of main actors (the rest is visible when clicked "show more actors")
NUMBER_OF_RELATED_FILMS = 6 # max no of films related to the current one (on film page)

MAX_USERNAME_LENGTH_DISPLAY = 13 # when displaying user names we display only the first X characters - this defines the X

FOLLOWED_USERS_FOR_WIDGET = 12
FOLLOWED_USERS_FOR_PAGE = 20

NUMBER_OF_USER_BEST_FILMS = 6
MIN_FILM_COMPARATOR_SCORE = '0.23'

RECOMMENDED_USERS = ('Esme', 'lamijka', 'verdiana', 'ayya', 'doktor_pueblo', 'lapsus', 'aiczka', 'kw86', 'michuk', 'queerdelys', 'umbrin', 'chinina_dla_nel', 'inheracil', 'wks', 'mazureQ', 'Habdank')
SUGGESTED_USERS = ('michuk', 'adz')

AVATAR_SIZES = (180, 128, 96, 72, 45, 32)
CACHE_AVATARS = True

DEFAULT_MAX_COMMENT_DEPTH = 2
DEFAULT_MARKUP = 5

LOGIN_REDIRECT_URL = "/"

ACCOUNT_ACTIVATION_DAYS = 14

I18N_URLS = True

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

LOCALE_PATHS = (
    ABS_DIR("locale"),
)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ABS_DIR('static/')

DEFAULT_AVATAR = ABS_DIR('static/avatars-dev/generic.96.jpg')
DEFAULT_POSTER = "img/default_poster.png"
DEFAULT_PHOTO = "img/default_actor.png"

POSTER_DIMENSION = ( 600, 900 )
POSTER_MIN_DIMENSION = ( 180, 270 )

CREATE_THUMBNAILS = True
POSTER_THUMBNAIL_SIZES = (
        (180, 'auto'), # film page size
        (100, 'auto'), # other pages
        (50, 'auto'),  # old filmaster size
)

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = MEDIA_URL + 'grappelli/'

# imdb fetcher configuration stuff - TODO: check if this is at all needed
MOVIE_DIRECTORY = "./import/films/"
PEOPLE_DIRECTORY = "./import/people/"
MOVIE_LIST_FILE = "movie_list.txt"
IDS_LIST_FILE = "ids_list.txt"
DATABASE_URI = "mysql://imdbuser:imdbpass@localhost/imdb"

OAUTH_AUTH_VIEW = "film20.api.views.oauth_auth"
OAUTH_CALLBACK_VIEW = "film20.api.views.oauth_pin"

APNS_SANDBOX = True
APNS_SENDMAIL = False
# apns certificate absolute path, defaults to notification/apns_cert.pem
# APNS_CERTIFICATE = ...

GEOIP_PATH = MEDIA_ROOT + 'GeoLiteCity.dat'

REGIONS = {
'23': u'lubelskie',
'24': u'podlaskie',
'25': u'podlaskie',
'26': u'kujawsko-pomorskie',
'27': u'lubelskie',
'28': u'wielkopolskie',
'29': u'slaskie',
'30': u'warminsko-mazurskie',
'31': u'pomorskie',
'32': u'lubuskie',
'33': u'dolnoslaskie',
'34': u'wielkopolskie',
'35': u'slaskie',
'36': u'swietokrzyskie',
'37': u'wielkopolskie',
'38': u'zachodniopomorskie',
'39': u'malopolskie',
'40': u'podkarpackie',
'41': u'dolnoslaskie',
'42': u'dolnoslaskie',
'43': u'lodzkie',
'44': u'podlaskie',
'45': u'lubelskie',
'46': u'malopolskie',
'47': u'warminsko-mazurskie',
'48': u'opolskie',
'49': u'mazowieckie',
'50': u'wielkopolskie',
'51': u'lodzkie',
'52': u'mazowieckie',
'53': u'wielkopolskie',
'54': u'podkarpackie',
'55': u'mazowieckie',
'56': u'podkarpackie',
'57': u'mazowieckie',
'58': u'lodzkie',
'59': u'lodzkie',
'60': u'pomorskie',
'61': u'podlaskie',
'62': u'zachodniopomorskie',
'63': u'swietokrzyskie',
'64': u'malopolskie',
'65': u'kujawsko-pomorskie',
'66': u'dolnoslaskie',
'67': u'mazowieckie',
'68': u'kujawsko-pomorskie',
'69': u'dolnoslaskie',
'70': u'lubelskie',
'71': u'lubuskie',
'72': u'dolnoslaskie',
'73': u'kujawsko-pomorskie',
'74': u'lodzkie',
'75': u'lubelskie',
'76': u'lubuskie',
'77': u'malopolskie',
'78': u'mazowieckie',
'79': u'opolskie',
'80': u'podkarpackie',
'81': u'podlaskie',
'82': u'pomorskie',
'83': u'slaskie',
'84': u'swietokrzyskie',
'85': u'warminsko-mazurskie',
'86': u'wielkopolskie',
'87': u'zachodniopomorskie',
}

# sequence of (UserAgent regex, platform name) tuples
USER_AGENTS = (
    (r'iPhone', 'iphone'),
    (r'iPod', 'ipod'),
    (r'Android', 'android'),
)

HAYSTACK_CUSTOM_HIGHLIGHTER = 'film20.search.utils.SolrHighlighter'
HAYSTACK_SEARCH_ENGINE = 'film20.search.backends.custom_solr'
HAYSTACK_SITECONF = 'film20.search.search_sites'
HAYSTACK_SOLR_URL = 'http://127.0.1:8983/solr'
HAYSTACK_INCLUDE_SPELLING = False
HAYSTACK_DEFAULT_OPERATOR = 'OR'
HAYSTACK_SILENTLY_FAIL = False


BROKER_HOST = "127.0.0.1"
BROKER_PORT = 5672
BROKER_VHOST = "/"
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"

CELERY_DEFAULT_QUEUE = "default"   
CELERY_DEFAULT_EXCHANGE = "default"
CELERY_DEFAULT_EXCHANGE_TYPE = "topic"
CELERY_DEFAULT_ROUTING_KEY = "default"

CELERYD_CONCURRENCY = 2

EMAIL_HOST='localhost'
EMAIL_HOST_USER=''
EMAIL_HOST_PASSWORD=''
EMAIL_PORT='25'

EMAIL_DOMAIN = 'localhost'
DOMAIN = 'localhost:8000'

#SESSION_COOKIE_DOMAIN = '.%(DOMAIN)s'
FULL_DOMAIN = 'http://%(DOMAIN)s'
BLOG_DOMAIN = 'http://blog.%(DOMAIN)s'
BLOG_FEED = '%(BLOG_DOMAIN)s/feed/'

ANALYTICS_CODE = 'NONE'

DEFAULT_FROM_EMAIL = "admin@%(EMAIL_DOMAIN)s"
SERVER_EMAIL = "admin@%(EMAIL_DOMAIN)s"
CONTACT_EMAIL = "filmaster@%(EMAIL_DOMAIN)s"

EMAIL_CONFIRMATION_DAYS = 14

FORCE_LOWERCASE_TAGS = True
SHORT_FILM_TAGS = (u'short', u'krótkometrażowy')

OEMBED_MAX_WIDTH = 300
OEMBED_MAX_HEIGHT = 200

# facebook apps: http://www.facebook.com/developers/apps.php
FACEBOOK_CONNECT_KEY = ''
FACEBOOK_CONNECT_SECRET = ''
FACEBOOK_PERMS = "offline_access,publish_stream,email"
FACEBOOK_CONNECT_HTTPONLY = 0

# twitter apps: http://dev.twitter.com/apps
TWITTER_KEY = ""
TWITTER_SECRET = ""

TWITTER_STREAM = True

# foursquare apps: https://foursquare.com/oauth/
FOURSQUARE_KEY = ""
FOURSQUARE_SECRET = ""

FAKE_IP = None # for geoip testing
GEONAMES_USERNAME = "filmaster"

FBAPP_CONNECT_KEY = ""
FBAPP_CONNECT_SECRET = ""

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)5s:%(name)s - %(message)s - @%(funcName)s/%(lineno)d'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console':{
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
#        'file': {
#            'level': 'DEBUG',
#            'formatter': 'verbose',
#            'class': 'logging.handlers.TimedRotatingFileHandler',
#            'filename': '/var/log/filmaster.log',
#            'when': 'D',
#            'interval': 1,
#            'backupCount': 7,
#        },
    },
    'loggers': {
        'django': {
            'handlers':['null'],
            'propagate': True,
            'level':'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'film20': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'filters': []
        },
        'film20.utils.cache': {
            'level':'WARNING',
        }
    }
}

FILE_UPLOAD_MAX_MEMORY_SIZE = 20 * 10**6

# TODO - investigate why test fails when True
SOUTH_TESTS_MIGRATE = False

# old style permalinks - can be set to False when we say goodbye to the old website
ENSURE_OLD_STYLE_PERMALINKS = False
DOMAIN_OLD = "filmaster.pl"
FULL_DOMAIN_OLD = "http://" + DOMAIN_OLD

# place postprocess_settings(globals()) call on the end of settings.py

CELERY_QUEUE_PREFIX = ""

SKIP_EXTERNAL_REQUESTS = False

BETA_CREDENTIALS = None # or string "user:password"

# experimental feature - cache logged in user in authentication middleware
# so we have one less db hit on each page
CACHED_USERS = False

FORCE_OAUTH_THEME = None # 'iphone' or 'android'

SHOWTIMES_PAST_SECONDS = 9000 #2.5h

# StatsMiddleware 
REQUEST_TIME_WARNING_THRESHOLD = 2000
NUM_QUERIES_WARNING_THRESHOLD = 20

CAN_SKIP_CACHE = True

DAY_START_HOUR = 4
INTEGRATION_TESTS = True

#RECOMMENDATIONS_ENGINE = 'film20.new_recommendations.recommendations_engine'
RECOMMENDATIONS_ENGINE = 'film20.recommendations.recommendations_engine'

RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''

SUGGEST_SIMILAR_FILMS = True
NUMBER_OF_SUGGESTED_SIMILAR_FILMS = 5

VUE_MIN_KNOWN_FILMS_NR = 1000 # 0 means only films similar to vue
VUE_RATER_SHUFFLE_BLOCK_SIZE = 100
VUE_DEBUG = False

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 1

USE_REDIS = True

TEST_RUNNER = 'film20.utils.test.TestRunner'

STATIC_URL = MEDIA_URL
GRAPPELLI_ADMIN_TITLE = 'FILMASTER 2.0'

SOLR_TESTS = True
FORCE_SSL_LOGIN = False

def postprocess_settings(globals):
    import re
    RE = re.compile(r"%\([A-Z_]+\)s")
    for k, v in list(globals.items()):
        if isinstance(v, basestring) and RE.search(v):
            globals[k] = v % globals

    try:
        import djcelery
        djcelery.setup_loader()
    except ImportError:
        pass

    CELERY_QUEUE_PREFIX = globals['CELERY_QUEUE_PREFIX']
    LANGUAGE_CODE = globals['LANGUAGE_CODE'] 
    CELERY_DEFAULT_QUEUE = CELERY_QUEUE_PREFIX + LANGUAGE_CODE + ".default"
    
    CELERY_QUEUES = {
        CELERY_DEFAULT_QUEUE: {
            "binding_key": CELERY_DEFAULT_QUEUE,
        },
        CELERY_QUEUE_PREFIX + LANGUAGE_CODE + ".notice": {
            "binding_key": CELERY_QUEUE_PREFIX + LANGUAGE_CODE + ".notice.#",
        },
        CELERY_QUEUE_PREFIX + LANGUAGE_CODE + ".massemail": {
            "binding_key": CELERY_QUEUE_PREFIX + LANGUAGE_CODE + ".massemail.#",
        },
        CELERY_QUEUE_PREFIX + LANGUAGE_CODE + ".recommendations": {
            "binding_key": CELERY_QUEUE_PREFIX + LANGUAGE_CODE + ".recommendations.#",
        },
    }
    
    CELERY_MASSMAIL_TASK_CONFIG = {
        'routing_key' : CELERY_QUEUE_PREFIX + LANGUAGE_CODE + ".massemail.email",
    }

    globals['CELERY_QUEUES'] = CELERY_QUEUES
    globals['CELERY_DEFAULT_QUEUE'] = CELERY_DEFAULT_QUEUE
    globals['CELERY_MASSMAIL_TASK_CONFIG'] = CELERY_MASSMAIL_TASK_CONFIG

    globals['COUNTRY_CODE'] = globals['COUNTRY_CODE'].upper()

    # TODO - remove key_func along with cache KEY_PREFIX option
    # (it is redundand as cache.Key add site prefix too)
    
    from django.utils.encoding import smart_str
    def key_func(key, prefix, version):
        if key.startswith('common_'):
            prefix = 'common'
        return ':'.join((prefix, str(version), smart_str(key)))

    globals['CACHES']['default']['KEY_FUNCTION'] = key_func

