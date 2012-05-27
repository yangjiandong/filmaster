from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.db.models import Q
#from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import resolve, reverse as django_reverse
from django.core import signals
from django.http import Http404
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models.query import QuerySet
from django.views.decorators.cache import never_cache

from piston.handler import BaseHandler as PistonBaseHandler, TypeMapper
from piston.resource import Resource as PistonResource
from piston.utils import rc
from piston.authentication import OAuthAuthentication, HttpBasicAuthentication, \
                                  NoAuthentication

from film20.core.models import Object, Profile, Rating,\
                               Film, Person, PersonLocalized, Character, ShortReview,\
                               RatingComparator
from film20.externallink.models import ExternalLink
from film20.messages.models import Message, Conversation
from film20.filmbasket.models import BasketItem
from film20.userprofile.models import Avatar
from film20.userprofile.forms import ProfileForm
from film20.api.utils import paginated_collection, collection, \
                             debug_call, form_errors, get_list, get_request, set_request, JSONEmitter, strip_html, get_hires_image
                             
from film20.recommendations.recom_helper import RecomHelper, FILMASTERS_ALL, FOLLOWING_ONLY
from film20.search import search, search_user, search_film, search_person
from film20.core.film_helper import FilmHelper
from film20.core import rating_helper
from film20.useractivity.useractivity_helper import PlanetHelper

from film20.core.film_forms import ShortReviewForm
from film20.utils.slughifi import slughifi
from film20.blog.models import Post, Blog
from film20.blog.forms import BlogPostForm
from film20.threadedcomments.models import ThreadedComment
from film20.threadedcomments.forms import ThreadedCommentForm
from film20.useractivity.models import UserActivity
from film20.messages.forms import ComposeForm
from film20.showtimes.models import Channel, Screening, FilmScreenings, ChannelScreenings, FilmScreeningsChannel, ChannelScreeningsFilm,\
                             ScreeningCheckIn, Town, Country, FilmOnChannel, UserChannel,\
                             TYPE_CINEMA, TYPE_TV_CHANNEL
from film20.showtimes import showtimes_helper
from film20.showtimes.showtimes_helper import ScreeningSet
from film20.showtimes.utils import get_available_showtime_dates, parse_date
from film20 import recommendations

from film20.config import urls

import datetime
import logging
logger = logging.getLogger(__name__)

recom_helper = RecomHelper()
film_helper = FilmHelper()
planet_helper = PlanetHelper()

typemapper = TypeMapper()

class SessionAuthentication(object):
    def is_authenticated(self, request):
        return request.user.is_authenticated()

    def challenge(self):
        pass

AUTHORIZED = (SessionAuthentication(), OAuthAuthentication(), HttpBasicAuthentication())
ANONYMOUS = (NoAuthentication(),)

_ = lambda x:x

VERSION_PREFIX = "/1.1"

def get_request_includes(request):
    if not hasattr(request, '_includes'):
        parsed = (tuple(i.split('.')) for i in request.GET.get('include', '').split(','))
        request._includes = set(x for x in parsed if x)
    return request._includes

class Resource(PistonResource):
    @classmethod
    def register_anonymous(cls, handler):
        authorized = type(handler.__name__ + "Anon", (handler,), {
            'is_anonymous':False,
            'anonymous':handler,
        })
        return cls(authorized, AUTHORIZED)

    @classmethod
    def mapper(cls):
        return typemapper

    def __call__(self, request, *args, **kw):
        #arrgh, include hack
        set_request(request)
        return super(Resource, self).__call__(request, *args, **kw)

    @staticmethod
    def cleanup_request(request):
        # force empty dictionary id request.data is not dict-like object
        if not hasattr(getattr(request, 'data', None), "get"):
            request.data = {}
        return PistonResource.cleanup_request(request)
        
    def error_handler(self, e, request, meth, em_format):
        if not isinstance(e, Http404):
            # signal exception (for unittest report)
            receivers = signals.got_request_exception.send(sender=self.__class__, request=request)
            logger.exception(e)
        return super(Resource, self).error_handler(e, request, meth, em_format)

class BaseHandler(PistonBaseHandler):
    @classmethod
    def get_fields(cls, emitter):
        request = get_request()
        path = tuple(getattr(emitter, 'path', ()))
        
        if path and path[0]=='objects':
            path = path[1:]

        if not request:
            return cls.fields
        includes = tuple(i[-1] for i in get_request_includes(request) if i[:-1] == path)
        if hasattr(cls, 'include_fields'):
            includes = tuple(set(includes).intersection(cls.include_fields))
          
        return tuple(cls.fields) + includes

    @classmethod
    def mapper(cls):
        return typemapper

class AnonymousBaseHandler(BaseHandler):
    is_anonymous = True
    allowed_methods = ('GET',)
    
def reverse(view, *args, **kw):
    import urls
    return VERSION_PREFIX + django_reverse(view, urlconf=urls, *args, **kw)

def uri(method):
    @classmethod
    def wrapper(cls, obj):
        ret = method(cls, obj)
        return ret and reverse(ret[0], args=ret[1]) or ret
    return wrapper

def static_image(method):
    @classmethod
    def wrapper(cls, obj):
        image = method(cls, obj)
        return image and settings.MEDIA_URL + unicode(image) or ""
    return wrapper

def get_resource(request, resource_uri, **kwargs):
    if resource_uri and resource_uri.startswith(VERSION_PREFIX):
        import urls
        handler, args, kw = resolve(resource_uri[len(VERSION_PREFIX):], urlconf=urls)
        kw.update(kwargs)
        logger.info(handler.handler)
        return handler.handler.read(request, *args, **kw)

def BAD_REQUEST(data=None):
    resp = rc.BAD_REQUEST
    if data:
        if isinstance(data, basestring):
            data = {'errors':[data]}
        resp.content = data
    return resp

def get_user(request, username):
    if request.user.is_authenticated() and request.user.username==username:
        return request.user
    else:
        return get_object_or_404(User, username=username)

def user_view(view):
    def wrapper(self, request, username=None, *args, **kw):
        if not username and not request.user.is_authenticated():
            return rc.FORBIDDEN
        request.username = username or request.user.username
        logger.info("username: %r", request.username)
        if not hasattr(request, 'uri_user'):
            if request.user.is_authenticated() and request.user.username == request.username:
                request.uri_user = request.user
            else:
                request.uri_user = username and get_object_or_404(User, username=username)
        return view(self, request, request.username, *args, **kw)
    return wrapper

def user_view_rw(view):
    @user_view
    def wrapper(self, request, username=None, *args, **kw):
        logger.info("username: %s %s", username, request.user.username)
        if username!=request.user.username:
            return rc.FORBIDDEN
        return view(self, request, username, *args, **kw)
    return wrapper
    
class AvatarHandler(AnonymousBaseHandler):
    model = Avatar
    fields = ('image', 'image_32', 'image_45', 'image_48', 'image_72', 'image_96', 'image_128')

    @classmethod
    def image(cls, avatar):
        return settings.MEDIA_URL + unicode(avatar.image)

    @classmethod
    def image_32(cls, avatar):
        return settings.MEDIA_URL + avatar.get_thumbnail_path(32)

    @classmethod
    def image_45(cls, avatar):
        return settings.MEDIA_URL + avatar.get_thumbnail_path(45)

    @classmethod
    def image_48(cls, avatar):
        return settings.MEDIA_URL + avatar.get_thumbnail_path(48)

    @classmethod
    def image_72(cls, avatar):
        return settings.MEDIA_URL + avatar.get_thumbnail_path(72)

    @classmethod
    def image_96(cls, avatar):
        return settings.MEDIA_URL + avatar.get_thumbnail_path(96)

    @classmethod
    def image_128(cls, avatar):
        return settings.MEDIA_URL + avatar.get_thumbnail_path(128)

class AnonymousUserHandler(AnonymousBaseHandler):
    model = User
    fields = ('username',
              'display_name',
              'first_name',
              'last_name',
              'last_login',
              'date_joined',
              'avatar',
              'recommendations_uri',
              'recommendations_status',
              'ratings_uri',
              'films_unrated_uri',
              'filmbasket_uri',
              'wishlist_uri',
              'shitlist_uri',
              'films_owned_uri',
              'short_reviews_uri',
              'posts_uri',
              'activities_uri',
              'showtimes_uri',
              'channel_showtimes_uri',
              'channels_uri',
              'community_uri',
              'checkin_uri',
              'latitude',
              'longitude',
              'timezone',
              'country',
              'location',
              'website', 
              'unread_conversation_cnt',
              'recommendations_status',
              'films_rated_cnt',
              'description',
              'gender')

    include_fields = ('common_taste', 'distance')
    
    @classmethod
    def avatar(cls, user):
        try:
            return Avatar.objects.get(user=user, valid=True)
        except Avatar.DoesNotExist:
            return Avatar(user=user, 
                          valid=True, 
                          date=datetime.date.today(),
                          image='avatars/generic.jpg')

    @uri
    def filmbasket_uri(cls, user):
        return 'user_basket_handler', [user.username]

    @uri
    def shitlist_uri(cls, user):
        return 'user_shitlist_handler', [user.username]

    @uri
    def wishlist_uri(cls, user):
        return 'user_wishlist_handler', [user.username]

    @uri
    def films_owned_uri(cls, user):
        return 'user_films_owned_handler', [user.username]

    @uri
    def recommendations_uri(cls, user):
        return user_recommendations_handler, [user.username]

    @uri
    def ratings_uri(cls, user):
        return film_ratings_handler, [user.username]

    @uri
    def short_reviews_uri(cls, user):
        return user_short_reviews_handler, [user.username]

    @uri
    def films_unrated_uri(cls, user):
        return user_unrated_films_handler, [user.username]
    
    @uri
    def activities_uri(cls, user):
        return user_activity_handler, [user.username]
    
    @uri
    def posts_uri(cls, user):
        return user_post_handler, [user.username]
    
    @classmethod
    def website(cls, user):
        return user.get_profile().website

    @classmethod
    def website(cls, user):
        return user.get_profile().website

    @classmethod
    def description(cls, user):
        return strip_html(user.get_profile().get_localized_profile().description)

    @classmethod
    def gender(cls, user):
        return user.get_profile().gender

    @user_view
    def read(self, request, username=None):
        return get_user(request, username)
    
    @classmethod
    def latitude(cls, user):
        return user.get_profile().latitude

    @classmethod
    def longitude(cls, user):
        return user.get_profile().longitude

    @classmethod
    def timezone(cls, user):
        return user.get_profile().timezone_id
    
    @classmethod
    def country(cls, user):
        return user.get_profile().country

    @classmethod
    def location(cls, user):
        return user.get_profile().location
        
    @uri
    def showtimes_uri(cls, user):
        return user_showtimes_handler, [user.username]

    @uri
    def channels_uri(cls, user):
        return user_channel_handler, [user.username]

    @uri
    def channel_showtimes_uri(cls, user):
        return user_channel_showtimes_handler, [user.username]
        
    @uri
    def community_uri(cls, user):
        return user_community_handler, [user.username]

    @uri
    def checkin_uri(cls, user):
        return user_checkin_handler, [user.username]

    @classmethod
    def unread_conversation_cnt(cls, user):
        return user.unread_conversation_counter
    
    @classmethod
    def common_taste(cls, user):
        score = getattr(user, 'score', None)
        if score is None:
            request = get_request()
            if request.user.is_authenticated():
                if request.user == user:
                    score = 0
                else:
                    try:
                        rc = RatingComparator.objects.get(main_user=request.user, compared_user=user)
                        score = rc.score
                    except RatingComparator.DoesNotExist:
                        pass
        if score is not None:
            return "%.3f" % ((10 - score) * (10 - score) / 100)
    
    @classmethod
    def recommendations_status(cls, user):
        meta = user.get_profile()
        return meta.recommendations_status
    
    @classmethod
    def films_rated_cnt(cls, user):
        return Rating.count_for_user(user) or 0

    @classmethod
    def display_name(cls, user):
        return user.get_profile().display_name

from django import forms
class ApiProfileForm(ProfileForm):
    country = forms.CharField(max_length=2, required=False)
    latitude = forms.DecimalField(required=False)
    longitude = forms.DecimalField(required=False)
    iphone_token = forms.CharField(max_length=64, required=False)
    location = forms.CharField(max_length=255, required=False)
    
    def clean_country(self):
        # TODO - country code checking
        return self.cleaned_data['country'].upper()
    
    class Meta:
        model = Profile
        fields = ProfileForm.Meta.fields + (
            'country', 'latitude', 'longitude', 'iphone_token', 'location',
        )
    
class UserHandler(AnonymousUserHandler):
    anonymous = AnonymousUserHandler
    is_anonymous = False
    allowed_methods = ('GET', 'PUT',)
    
    @user_view_rw
    def update(self, request, username=None):
        user = get_user(request, username)
        request_data = request.data
        localized_profile = user.get_profile().get_localized_profile()
        data = model_to_dict(user.get_profile())
        data.update(model_to_dict(user))
        data.update(model_to_dict(localized_profile))
        data.update(request_data.items())

        form = ApiProfileForm(data, instance=user.get_profile())
        if form.is_valid():
            profile = form.save(commit=False)
            if 'iphone_token' in request_data:
                profile.set_iphone_token(form.cleaned_data.get('iphone_token'))
            profile.save()
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            localized_profile.description = form.cleaned_data['description']
            localized_profile.save()
            return user
        else:
            logger.error(form_errors(form))
            return BAD_REQUEST(form_errors(form))

class ExternalLinkHandler(AnonymousBaseHandler):
    model = ExternalLink
    fields = ['url', 'updated_at', 'created_at', 'url_kind']

    def read(self, request, id):
        return get_object_or_404(ExternalLink.objects, id=id)

class AnonPersonHandler(AnonymousBaseHandler):
    model = Person
    fields = ['name', 'surname', 'image', 'hires_image', 'permalink', 
#            'gender', 'day_of_birth', 'year_of_birth', 'month_of_birth', 
              'films_played_uri', 'films_directed_uri', 'posts_uri']

    @uri
    def resource_uri(cls, person):
        return person_handler, [person.permalink]
    
    @uri
    def films_played_uri(cls, person):
        return films_played_handler, [person.permalink]

    @uri
    def films_directed_uri(cls, person):
        return films_directed_handler, [person.permalink]

    @uri
    def posts_uri(self, person):
        return person_posts_handler, [person.permalink]

    @classmethod
    def posts(cls, person):
        return person.related_people.all()

    @classmethod
    def posts_cnt(cls, person):
        return cls.posts(person).count()

    @classmethod
    def has_posts(cls, person):
        return bool(cls.posts_cnt(person))
    
    def read(self, request, permalink):
        return get_object_or_404(Person, permalink=permalink)

    @classmethod
    def image(cls, person):
        if person.image:
            return u"%s%s" % (settings.MEDIA_URL, person.image)
        else:
            return urls.urls.get('DEFAULT_ACTOR')

    @classmethod
    def hires_image(cls, person):
        return get_hires_image(person)
    
    @classmethod
    def name(cls, person):
        return person.localized_name
    
    @classmethod
    def surname(cls, person):
        return person.localized_surname

class PersonHandler(AnonPersonHandler):
    anonymous = AnonPersonHandler
    is_anonymous = False
    allowed_methods = ('GET', 'PUT')

    def update(self, request, permalink):
        person = get_object_or_404(Person.objects.select_related(), permalink=permalink)
        if 'tags' in request.data:
            if not request.user.has_perm('core.can_edit_tags'):
                return rc.FORBIDDEN
            person.save_tags(request.data['tags'])
        if 'name' in request.data or 'surname' in request.data:
            if not request.user.has_perm('core.can_edit_description'):
                return rc.FORBIDDEN
            name = request.data.get('name', person.name)
            surname = request.data.get('surname', person.surname)
            localized, created = PersonLocalized.objects.get_or_create(
                person=person,
                parent=person,
                defaults = {
                    'name':name,
                    'surname':surname,
                },
            )
            if not created:
                localized.name = name
                localized.surname = surname
                localized.save()
        return person

class AnonFilmHandler(AnonymousBaseHandler):
    model = Film
    fields = ('image', 'hires_image', 'permalink', 'production_country_list', 'wishlist',
              'release_date', 'release_year', 'title', 'title_localized', 'description',
              'directors', 'characters_uri', 'links_uri', 'video_uri', 'tags', 'related_uri',
              'short_reviews_uri', 'posts_uri', 'average_score', 'number_of_votes',
              'checkin_uri', 'guess_rating', 'netflix_id', 'netflix_instant', 'length')
    @uri
    def resource_uri(cls, film):
        return film_handler, [film.permalink]
      
    @uri
    def characters_uri(cls, film):
        return film_characters_handler, [film.permalink]

    @classmethod
    def basket(cls, film):
        return hasattr(film, 'basket') and film.basket or None
        
    @uri
    def related_uri(cls, film):
        return film_related_handler, [film.permalink]
                
    @classmethod
    def title_localized(self, film):
        return film.pk and film.get_localized_title() or film.title
    
    @classmethod
    def description(self, film):
        descr = film.get_description()
        if not descr:
            localized_film = film.get_localized_film()
            descr = localized_film and localized_film.fetched_description or ''
        return strip_html(descr)
    
    @classmethod
    def directors(self, film):
        return film.pk and film.directors.all() or QuerySet().none()
    
    @classmethod
    def links(cls, film):
        return film.pk and film.film_link.all() or QuerySet().none()

    @classmethod
    def links_cnt(cls, film):
        return cls.links(film).count()

    @classmethod
    def has_links(cls, film):
        return bool(cls.links_cnt(film))

    @uri
    def links_uri(cls, film):
        return film_links_handler, [film.permalink]

    @classmethod
    def video(cls, film):
        return film.pk and film.get_videos() or QuerySet().none()

    @classmethod
    def video_cnt(cls, film):
        return cls.video(film).count()

    @classmethod
    def has_video(cls, film):
        return bool(cls.video_cnt(film))

    @uri
    def video_uri(cls, film):
        return film_links_handler, [film.permalink, 'video']
    
    @classmethod
    def tags(self, film):
        tags = film.pk and film.get_tags() or ''
        return [s.strip() for s in tags.split(',') if s]

    def read(self, request, permalink):
        unmatched = permalink.startswith('unmatched-film-')
        if unmatched:
            f = get_object_or_404(FilmOnChannel, pk=permalink[15:])
            film = showtimes_helper.film_from_film_on_channel(f)
        else:
            film = get_object_or_404(Film.objects.select_related(), permalink=permalink)
        return film
    
    @uri
    def short_reviews_uri(self, film):
        return film_short_reviews_handler, [film.permalink]

    @classmethod
    def short_reviews(cls, film):
        return film.pk and ShortReview.objects.filter(object__type=Object.TYPE_FILM,
                                             object__permalink=film.permalink,
                                            ).order_by('-created_at').select_related('user', 'object') or QuerySet().none()

    @classmethod
    def short_reviews_cnt(cls, film):
        return cls.short_reviews(film).count()
    
    @classmethod
    def has_short_reviews(cls, film):
        return bool(cls.short_reviews_cnt(film))
    
    @uri
    def posts_uri(cls, film):
        return film_posts_handler, [film.permalink]
    
    @classmethod
    def posts(cls, film):
        return film.pk and film.related_film.all() or QuerySet().none()

    @classmethod
    def posts_cnt(cls, film):
        return cls.posts(film).count()

    @classmethod
    def has_posts(cls, film):
        return bool(cls.posts_cnt(film))
    
    #TODO - cache !
    @classmethod
    def auth_basket(self, film):
        if not film.pk: return None
        request = get_request()
        if request.user.is_authenticated():
            item = get_basket_item(film, request.user.username)
            logger.info("basket item: %r, user: %r", item, request.user)
            return item

    @classmethod
    def basket(self, film):
        if not film.pk: return None
        request = get_request()
        username = getattr(request, 'username', None)
        if username:
            return get_basket_item(film, username)

    @classmethod
    def auth_rating_list(self, film):
        if not film.pk: return ()
        request = get_request()
        if request.user.is_authenticated():
            return get_rating_list(film, request.user_id)

    @classmethod
    def rating_list(self, film):
        if not film.pk: return ()
        request = get_request()
        username = getattr(request, 'username', None)
        if username:
            return get_rating_list(film, username)

    @classmethod
    def guess_rating(cls, film):
        if not film.pk: return None
        request = get_request()
        if request.user.is_authenticated():
            if not hasattr(film, 'guess_rating'):
                film.guess_rating = recommendations.engine.compute_guess_score(request.user, film.pk)
            return film.guess_rating

    auth_guess_rating = guess_rating

    @classmethod
    def image(cls, film):
        return get_hires_image(film, ('100', 'auto'))

    @classmethod  
    def hires_image(cls, film):
        return get_hires_image(film)

    @classmethod
    def production_country_list(cls, film):
        return film.production_country_list and [s.strip() for s in film.production_country_list.split(',') if s] or ()

    @classmethod
    def average_score(cls, film):                
        return film.pk and film.average_score() or None

    @classmethod
    def number_of_votes(cls, film):                
        return film.pk and film.number_of_votes() or None
    
    @uri
    def checkin_uri(cls, film):
        return film_checkin_handler, [film.permalink]

    @classmethod
    def auth_checked_in(cls, film):
        request = get_request()
        if request.user.is_authenticated():
            # TODO - cache !
            return bool(ScreeningCheckIn.objects.filter(user=request.user, film=film))

    # workaround for strange 'include=film.film' in requests
    @classmethod
    def film(cls, film):
        return film

class FilmHandler(AnonFilmHandler):
    anonymous = AnonFilmHandler
    is_anonymous = False
    allowed_methods = ('GET', 'PUT')

    def update(self, request, permalink):
        film = get_object_or_404(Film.objects.select_related(), permalink=permalink)
        if 'tags' in request.data:
            if not request.user.has_perm('core.can_edit_tags'):
                return rc.FORBIDDEN
            film.save_tags(request.data['tags'])
        if 'description' in request.data:
            if not request.user.has_perm('core.can_edit_description'):
                return rc.FORBIDDEN
            film.save_description(request.data['description'])
        return film
    
                
class FilmRelatedHandler(AnonymousBaseHandler):
    def read(self, request, permalink):
        film = get_object_or_404(Film, permalink=permalink)
        NUMBER_OF_RELATED_FILMS = getattr(settings, "NUMBER_OF_RELATED_FILMS", 6)
        related = film_helper.get_related_localized_objects(film, NUMBER_OF_RELATED_FILMS)
        return collection(request, [o.parent.get_film() for o in related])

class FilmLinksHandler(AnonymousBaseHandler):
    def read(self, request, permalink, type=None):
        film = get_object_or_404(Film, permalink=permalink)
        collection = film.film_link.all()
        if type=='video':
            collection = FilmHandler.video(film)
        elif type:
            collection = film.film_link.filter(url_kind=int(type))
        else:
            collection = film.film_link.all()
        return paginated_collection(request, collection)        
  
class CharacterHandler(AnonymousBaseHandler):
    model = Character
    fields = ['importance', 'character', 'person']
    
    @uri
    def person_uri(self, character):
        return person_handler, [character.person.permalink]

class FilmCharactersHandler(AnonymousBaseHandler):
    def read(self, request, permalink):
        film = get_object_or_404(Film.objects.select_related(), permalink=permalink)
        return paginated_collection(request, film.get_actors())

class FilmsPlayedHandler(AnonymousBaseHandler):
    def read(self, request, permalink):
        person = get_object_or_404(Person, permalink=permalink)
        return paginated_collection(request, person.films_played.distinct().order_by('-release_year','title'))

class FilmsDirectedHandler(AnonymousBaseHandler):
    def read(self, request, permalink):
        person = get_object_or_404(Person, permalink=permalink)
        return paginated_collection(request, person.films_directed.distinct().order_by('-release_year','title'))

def follower(request, username, peer, view):
    includes = get_request_includes(request)
    logger.info(includes)
    data = {
        'resource_uri': reverse(view, args=[username, peer.username]),
        'user_uri':reverse(user_handler, args=[peer.username]),
    }
    if ('user',) in includes:
        data['user'] = peer
    if ('avatar',) in includes:
        data['avatar'] = UserHandler.avatar(peer)
    return data

class AnonAbstractFollowersHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username, peername=None):
        wrap = lambda i:follower(request, username, i, self.get_handler())
        user = get_object_or_404(User, username=username)
        collection = self.filter(user.followers)
        if peername:
            return wrap(get_object_or_404(collection, username=peername))
        return paginated_collection(request, collection, wrap)

class AbstractFollowersHandler(AnonAbstractFollowersHandler):
    is_anonymous = False
    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
    
    @user_view_rw
    def create(self, request, username):
        user = get_object_or_404(User, username=username)
        peer_uri = request.data.get('user_uri')
        peer = get_resource(request, peer_uri)
        if peer == user:
            return BAD_REQUEST()
        self.create_follower(user, peer)
        return follower(request, username, peer, self.get_handler())

    @user_view_rw
    def update(self, request, username, peername):
        user = get_object_or_404(User, username=username)
        peer = get_object_or_404(User, username=peername)
        if peer == user:
            return BAD_REQUEST()
        self.create_follower(user, peer)
        return follower(request, username, peer, self.get_handler())

    @user_view_rw
    def delete(self, request, username, peername):
        user = get_object_or_404(User, username=username)
        peer = get_object_or_404(self.filter(user.followers), username=peername)
        user.followers.remove(peer)
        return follower(request, username, peer, self.get_handler())

class FollowingMixin(object):
    def get_handler(self): return user_following_handler
    def filter(self, q): return q.following()
    def create_follower(self, user, peer):
        user.followers.follow(peer)

class AnonUserFollowingHandler(AnonAbstractFollowersHandler, FollowingMixin):
    pass
    
class UserFollowingHandler(AbstractFollowersHandler, FollowingMixin):
    anonymous = AnonUserFollowingHandler

class FollowersMixin(object):
    def get_handler(self): return user_followers_handler
    def filter(self, q): return q.followers()

class UserFollowersHandler(AnonAbstractFollowersHandler, FollowersMixin):
    pass
    
class BlockingMixin(object):
    def get_handler(self): return user_blocking_handler
    def filter(self, q): return q.blocking()
    def create_follower(self, user, peer):
        user.followers.block(peer)

class AnonUserBlockingHandler(AnonAbstractFollowersHandler, BlockingMixin):
    pass
    
class UserBlockingHandler(AbstractFollowersHandler, BlockingMixin):
    anonymous = AnonUserBlockingHandler

class BlockersMixin(object):
    def get_handler(self): return user_blockers_handler
    def filter(self, q): return q.blockers()

class UserBlockersHandler(AnonAbstractFollowersHandler, BlockersMixin):
    pass

class FriendsMixin(object):
    def get_handler(self): return user_friends_handler
    def filter(self, q): return q.friends()

class UserFriendsHandler(AnonAbstractFollowersHandler, FriendsMixin):
    pass

class UserCommunityHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username):
        user = get_object_or_404(User, username=username)
        try:
            distance = int(request.GET.get('distance', 0))
        except ValueError:
            distance = 0
        type = FOLLOWING_ONLY if 'following' in request.GET else FILMASTERS_ALL
        sort_by = request.GET.get('sort_by', 'common_taste')
        if distance:
            result = recom_helper.get_nearby_users(user, distance, filmaster_type=type)
        else:
            result = recom_helper.get_best_tci_users(user, filmaster_type=type, sort_by=sort_by)
        return paginated_collection(request, result)
    
class AnonFilmRatingsHandler(AnonymousBaseHandler):
    model = Rating
    fields = ('type', 'rating', 'film_uri')
    @user_view
    def read(self, request, username, permalink=None):
        if permalink:
            ratings = Rating.objects.filter(film__permalink=permalink, user__username=username).select_related('film', 'user')
            return collection(request, ratings)
        else:
            user = get_user(request, username)
            ratings = recom_helper.get_all_ratings(user.id)
            return paginated_collection(request, ratings)

    @uri
    def film_uri(cls, item):
        return film_handler, [item.film.permalink]
    
    @uri
    def resource_uri(cls, item):
        return film_rating_handler, [item.user.username, item.film.permalink, item.type]

class FilmRatingsHandler(AnonFilmRatingsHandler):
    is_anonymous = False
    anonymous = AnonFilmRatingsHandler

class AnonFilmRatingHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username, permalink, type):
        return get_object_or_404(Rating, film__permalink=permalink, user__username=username, type=int(type), actor__isnull=True, director__isnull=True)

class FilmRatingHandler(AnonFilmRatingHandler):
    is_anonymous = False
    anonymous = AnonFilmRatingHandler
    allowed_methods = ('GET', 'PUT', 'DELETE')

    @user_view_rw
    def delete(self, request, username, permalink, type):
        film = get_object_or_404(Film, permalink=permalink)
        type = int(type)
        rating = get_object_or_404(Rating, user=request.user, parent=film.parent_id, type=type, actor__isnull=True, director__isnull=True)
        rating.delete()
        return rating

    VALID_RATINGS = [Rating.TYPE_FILM] + Rating.ADVANCED_RATING_TYPES
      
    @user_view_rw
    def update(self, request, username, permalink, type):
        film = get_object_or_404(Film, permalink=permalink)
        type = int(type)
        
        if type not in self.VALID_RATINGS:
            return BAD_REQUEST(_(u"invalid rating type"))
        
        try:
            rating = int(request.data.get('rating'))
            if not (1 <= rating <= 10):
                raise ValueError("Rating out of bounds")
        except (AttributeError, ValueError, TypeError), e:
            logging.exception(e)
            return BAD_REQUEST(_(u"invalid rating value"))

        rating_helper.rate(request.user, rating, film_id=film.id)
        r = Rating(user=request.user, film=film, parent=film, type=int(type), rating=rating)
        return r

def film_filter_kwargs(request):
    def dec(name):
        try:
            return int(request.GET.get(name))
        except TypeError, ValueError:
            return None

    def feat(name):
        try:
            return tuple(int(i) for i in request.GET.get(name, "").split(',') if i)
        except TypeError, ValueError:
            return ()

    director = list(get_resource(request, p) for p in request.GET.getlist('director_uri'))
    actor = list(get_resource(request, p) for p in request.GET.getlist('actor_uri'))

    kwargs = dict(
        tags = request.GET.get('tags'),
        year_from = dec('year_from'),
        year_to = dec('year_to'),
        related_director = director,
        related_actor = actor,
        popularity = dec('popularity'),
        include_features = feat('include_features'),
        exclude_features = feat('exclude_features'),
        exclude_production_country = request.GET.get('exclude_production_country') or \
                request.GET.get('production_country_list_exclude'),
        netflix = request.GET.get('netflix') or 'netflix' in request.GET,
    )
    return kwargs


class AnonUserRecommendationsHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username=None):
        user = get_object_or_404(User, username=username)

        recommended_films = recom_helper.get_best_psi_films_queryset(
            user,
            **film_filter_kwargs(request)
        )
        if not recommended_films:
            return FilmRankingHandler().read(request)
        return paginated_collection(request, recommended_films)

class UserRecommendationsHandler(AnonUserRecommendationsHandler):
    is_anonymous = False
    anonymous = AnonUserRecommendationsHandler

class FilmRankingHandler(AnonymousBaseHandler):
    def read(self, request):
        director = list(get_resource(request, p) for p in request.GET.getlist('director_uri'))
        actor = list(get_resource(request, p) for p in request.GET.getlist('actor_uri'))
        
        ranking = recom_helper.get_ranking(**film_filter_kwargs(request))

        def wrapper(rank):
            rank.film._rating = rank
            return rank.film
            
        return paginated_collection(request, ranking, wrapper)

#TODO cache !
def get_rating_list(film, user):
    kw = dict(film=film, actor__isnull=True, director__isnull=True)
    if isinstance(user, basestring):
        kw['user__username'] = user
    elif isinstance(user, (long, int)):
        kw['user'] = user
    else:
        assert False, "username or user_id expected"
    return [(r.type, r.rating) for r in Rating.objects.filter(**kw) if r.rating!=None]

#TODO cache !
def get_film_rating(film, user):
    kw = dict(film=film, type=Rating.TYPE_FILM, actor__isnull=True, director__isnull=True)
    if isinstance(user, basestring):
        kw['user__username'] = user
    elif isinstance(user, (long, int)):
        kw['user'] = user
    else:
        assert False, "username or user_id expected"
    try:
        return Rating.objects.get(**kw).rating
    except Rating.DoesNotExist:
        return None

def get_basket_item(film, username):
    basket_item = BasketItem.objects.user_items(basket_user=username, filter=film.permalink)
    basket_item = basket_item and basket_item[0] or None
    return basket_item


def sort_channels(request, channels):
    order = request.GET.get('channel_order')
    if order:
        desc = -1 if order[0] == '-' else 1
        if order[0] in ('-', '+'):
            order = order[1:]
        if order in ('name', ):
            key = lambda o: getattr(isinstance(o, UserChannel) and o.channel or o, order)
            _cmp = lambda a,b: desc * cmp(key(a),key(b))
            channels = sorted(channels, cmp=_cmp)
        logger.info("%r %r %r", desc, order, channels)
    return channels

def search_filter_kwargs(request):
    return dict( limit = request.GET.get('limit') )

def wrap_search(results):
    return dict(best_results=results[:3], results=results[3:])

class AnonUserFilmMetaHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username, permalink):
        include = get_request_includes(request)
        date = request.GET.get('date')
        try:
            date = date and parse_date(request, date)
        except ValueError:
            date = None
        town_uri = request.GET.get('town_uri')
        town = town_uri and get_resource(request, town_uri)
        
        user = get_user(request, username)
        unmatched = permalink.startswith('unmatched-film-')
        last_film_checkin_date = None
        if unmatched:
            f = get_object_or_404(FilmOnChannel, pk=permalink[15:])
            film = showtimes_helper.film_from_film_on_channel(f)
            basket_item = None
            rating = None
            has_short_review = False
            has_posts = False

            has_checkins = False
            has_film_checkins = False
        else:
            film = get_object_or_404(Film.objects.select_related(), permalink=permalink)
            # TODO
            basket_item = get_basket_item(film, username)
            has_short_review = bool(ShortReview.objects.filter(object__type=Object.TYPE_FILM,
                                                   object__permalink=film.permalink,
                                                   user=user).count())
            has_posts = bool(film.related_film.all()[0:1])
            checkins = ScreeningCheckIn.objects.filter(film=film, user=user)
            
            has_checkins = any(c for c in checkins if c.screening_id)
            has_film_checkins = any(c for c in checkins if not c.screening_id)
            if has_film_checkins:
                last_film_checkin_date = max(c.created_at for c in checkins if not c.screening_id)

        festival = get_festival(request)
        if date or festival:
            if festival:
                channels = festival.get_theaters()
            elif not town:
                channels = Channel.objects.selected_by(user, channel_type(request))
            else:
                channels = list(Channel.objects.theaters().in_town(town))
                if channel_type(request) & 2:
                    channels.extend(Channel.objects.selected_by(user, 2))
                    print channels
                
            channels = sort_channels(request, channels)

            if festival:
                from film20.festivals.models import FestivalScreeningSet
                if 'with_past' in request.GET:
                    kw = {'past':True}
                else:
                    kw = {}
                screening_set = festival.get_screening_set(**kw)
            else:
                screening_set = ScreeningSet(date, channels, **_showtimes_filter(request))

            channels = screening_set.get_channels(film.id or film.title)
            if festival and town:
                channels = filter(lambda c: c.town==town, channels)
            
            if festival and date:
                # festival sccreening set contains screenings from whole festival
                # filter out only screenings from specified day
                import pytz
                dfrom = date.astimezone(pytz.utc).replace(tzinfo=None)
                dto = dfrom + datetime.timedelta(days=1)
                filter_date = lambda screenings: [s for s in screenings if s.utc_time >= dfrom and s.utc_time <dto]
            else:
                filter_date = lambda screenings: screenings

            film_channels = [
                    FilmScreeningsChannel(channel=c, screenings=filter_date(c.screenings)) \
                            for c in channels]
        else:
            film_channels = None
            
        meta = {
            'film_uri': reverse(film_handler, args=[film.permalink]),
            'basket': basket_item,
            'guess_rating': recommendations.engine.compute_guess_score(user, film.pk),
            'rating_list':not unmatched and get_rating_list(film, username) or [],
            'has_short_review':has_short_review,
            'has_posts':has_posts,
            'has_checkins':has_checkins,
            'has_film_checkins':has_film_checkins,
            'last_film_checkin_date':last_film_checkin_date,
            'channels':film_channels,
        }
        if ('film',) in include:
            meta['film'] = film
        return meta

class UserFilmMetaHandler(AnonUserFilmMetaHandler):
    is_anonymous = False
    anonymous = AnonUserFilmMetaHandler

class AnonymousUserBasketItemHandler(AnonymousBaseHandler):
    model = BasketItem
    fields = ('owned', 'wishlist', 'resource_uri', 'film_uri')

    @user_view
    def read(self, request, username=None, permalink=None, type=None):
        if not permalink:
            return paginated_collection(request, BasketItem.objects.user_items(basket_user=username, type=type))
        items = BasketItem.objects.user_items(basket_user=username, type=type, filter=permalink)
        if not items:
            raise Http404
        elif len(items)==1:
            return items[0]
        assert False

    @uri
    def resource_uri(cls, item):
        return 'user_basketitem_handler', [item.user.username, item.film.permalink]
    
    @uri
    def film_uri(cls, item):
        return film_handler, [item.film.permalink]

class UserBasketItemHandler(AnonymousUserBasketItemHandler):
    is_anonymous = False
    allowed_methods = ('GET', 'POST', 'PUT', 'DELETE')
    anonymous = AnonymousUserBasketItemHandler

    @user_view_rw
    def delete(self, request, username, permalink, type=None):
        item = self.read(request, username, permalink, type)
        item.delete()
        return item

    def _update(self, request, item):
        data = request.data
        
        if 'owned' in data:
            item.owned = data.get('owned') or None
        if 'wishlist' in data:
            item.wishlist = data.get('wishlist') or None
        item.save()
        return item

    @user_view_rw
    def update(self, request, username, permalink, type=None):
        if type:
            # update only via filmbasket resource
            return BAD_REQUEST(_(u"update allowed only via filmbasket resource"))

        data = request.data
        film = get_object_or_404(Film, permalink=permalink)
        
        defaults = dict(
            user=request.user,
            owned=data.get('owned') or None,
            wishlist=data.get('wishlist') or None,
        )
        
        item = BasketItem.objects.user_items(basket_user=username, type=type, empty=True, filter=permalink)
        if len(item) == 0:
            user = User.objects.get(username__iexact=username)
            item = BasketItem(film=film, user=user)
        else:
            item = item[0]
            
        self._update(request, item)
        return item
    
    @user_view_rw
    def create(self, request, username):
        data = request.data
        film = get_resource(request, data.get('film_uri'))
        item = BasketItem(user=request.user, film=film)
        return self._update(request, item)

class AnonUnratedFilmsHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username):
        from film20.core import rating_helper
        user = get_user(request, username)
        rated_ids = set(rating_helper.get_user_ratings(user).keys())
        seen_ids = rating_helper.get_seen_films(user)

        kw = film_filter_kwargs(request)
#        if not 'popularity' in request.GET:
#            kw['popularity'] = 1
        films = recom_helper.get_ranking(**kw)
        films = films.exclude(film__in=rated_ids|seen_ids)
        
        def wrapper(rank):
            rank.film._rating = rank
            return rank.film
        
        return paginated_collection(request, films, wrapper)

class UnratedFilmsHandler(AnonUnratedFilmsHandler):
    is_anonymous = False
    anonymous = AnonUnratedFilmsHandler

class SearchFilmHandler(AnonymousBaseHandler):
    def read(self, request):
        return wrap_search(search_film(request.GET.get('phrase', ''), **search_filter_kwargs(request)))

class SearchPersonHandler(AnonymousBaseHandler):
    def read(self, request):        
        return wrap_search(search_person(request.GET.get('phrase', ''), **search_filter_kwargs(request)))

class SearchUserHandler(AnonymousBaseHandler):
    def read(self, request):
        return wrap_search(search_user(request.GET.get('phrase', ''), **search_filter_kwargs(request)))

class SearchTownHandler(AnonymousBaseHandler):
    def read(self, request):
        phrase = request.GET.get('phrase', '')
        country = request.GET.get('country', '').upper()
        if phrase:
            results = Town.objects.select_related().filter(name__istartswith=phrase)
            if country:
                results = results.filter(country__code=country)
        else:
            results = ()
        return paginated_collection(request, results)

class SearchHandler(AnonymousBaseHandler):
    def read(self, request):
        phrase = request.GET.get('phrase', '')
        return {
            'films':wrap_search(search_film(phrase, **search_filter_kwargs(request))),
            'persons':wrap_search(search_person(phrase, **search_filter_kwargs(request))),
            'users':wrap_search(search_user(phrase, **search_filter_kwargs(request))),
        }

class FilmShortReviewsHandler(AnonymousBaseHandler):
    def read(self, request, permalink):
        reviews = ShortReview.objects.filter(object__type=Object.TYPE_FILM,
                                             object__permalink=permalink,
                                            ).order_by('-created_at')
        reviews = reviews.select_related('user', 'object')
        return paginated_collection(request, reviews)

class AnonUserFilmShortReviewsHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username):
        reviews = ShortReview.objects.filter(user__username=username,
                                             object__type=Object.TYPE_FILM,
                                            ).order_by('-created_at')
        reviews = reviews.select_related('user', 'object', 'film')
        return paginated_collection(request, reviews)

class UserFilmShortReviewsHandler(AnonUserFilmShortReviewsHandler):
    anonymous = AnonUserFilmShortReviewsHandler
    is_anonymous = False

class AnonCommentHandler(AnonymousBaseHandler):
    model = ThreadedComment
    fields = ('comment', 'resource_uri', 'object_uri', 'parent_uri', 'date_modified', 'date_submitted')
    
    def read(self, request, id):
        comment = get_object_or_404(ThreadedComment, pk=id)
        return comment

    @uri
    def resource_uri(cls, comment):
        return comment_handler, [comment.pk]
    
    @uri
    def parent_uri(cls, comment):
        if comment.parent_id:
            return comment_handler, [comment.parent_id]
    
    @classmethod
    def object_uri(cls, comment):
        obj = comment.content_object
        if isinstance(obj, Post):
            return UserPostHandler.resource_uri(obj)
        if isinstance(obj, ShortReview):
            return UserFilmShortReviewHandler.resource_uri(obj)
        if isinstance(obj, ScreeningCheckIn):
            return CheckinHandler.resource_uri(obj)
        if isinstance(obj, UserActivity):
            return UserActivityHandler.resource_uri(obj)

    @classmethod
    def comment(cls, comment):
        return strip_html(comment.comment)
    
    @classmethod
    def level(cls, comment):
        return getattr(comment, 'depth', 0)
 
class CommentHandler(AnonCommentHandler):
    allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')
    is_anonymous = False
    anonymous = AnonCommentHandler
    
    def update(self, request, id):
        comment = self.read(request, id)
        if request.user != comment.user: return rc.FORBIDDEN

        data = model_to_dict(comment)
        data.update(request.data and request.data.items() or ())
        form = ThreadedCommentForm(data, instance=comment)
        
        if not form.is_valid(): 
            return BAD_REQUEST(form_errors(form))
        form.save()
        return comment
    
    def delete(self, request, id):
        comment = self.read(request, id)
        if request.user != comment.user: return rc.FORBIDDEN
        comment.delete()
        return comment

    def create(self, request):
        data = request.data
        form = ThreadedCommentForm(data)
        if not form.is_valid():
            logger.error('invalid form %r', form_errors(form))
            return BAD_REQUEST(form_errors(form))

        obj = get_resource(request, data.get('object_uri'))
        if not obj: 
            return BAD_REQUEST(_(u"object_uri is required"))
        
        if not isinstance(obj, UserActivity):
            try:
                obj = UserActivity.objects.get_for_object(obj)
            except UserActivity.DoesNotExist, e:
                raise Http404

        comment = form.save(commit=False)
        comment.content_type = ContentType.objects.get_for_model(obj)
        comment.object_id = obj.pk
        comment.comment = form.cleaned_data['comment']
        comment.parent = get_resource(request, data.get('parent_uri'))
        if comment.parent:
            assert comment.parent.object_id == comment.object_id and comment.parent.content_type_id == comment.content_type.id
        comment.ip_address = request.META.get('REMOTE_ADDR', None)
        comment.user = request.user
        comment.permalink = "COMMENT"
        comment.status = ThreadedComment.PUBLIC_STATUS
        comment.type = ThreadedComment.TYPE_COMMENT
        comment.save()

        return comment

class AnonBaseCommentsViewHandler(AnonymousBaseHandler):
    def read(self, request, *args, **kw):
        obj = self.get_object(*args, **kw)

        threaded = ('threaded' in request.GET)
        if threaded:
            comments = ThreadedComment.objects.get_tree(obj)
        else:
            comments = ThreadedComment.objects.filter(object_id=obj.pk).order_by('date_submitted')
            comments = comments.select_related('user')
        return paginated_collection(request, comments)

class UserPostCommentsHandler(AnonBaseCommentsViewHandler):
    def get_object(self, username, id):
        return get_object_or_404(UserActivity, username=username, post=id)

class UserWallPostCommentsHandler(AnonBaseCommentsViewHandler):
    def get_object(self, username, id):
        return get_object_or_404(UserActivity, username=username, short_review=id)

class UserShortReviewCommentsHandler(AnonBaseCommentsViewHandler):
    def get_object(self, username, permalink):
        return get_object_or_404(UserActivity, username=username, short_review__object__permalink=permalink)

class CheckinCommentsHandler(AnonBaseCommentsViewHandler):
    def get_object(self, id):
        return get_object_or_404(UserActivity, checkin=id)

class LinkCommentsHandler(AnonBaseCommentsViewHandler):
    def get_object(self, id):
        return get_object_or_404(UserActivity, link=id)

class RatingCommentsHandler(AnonBaseCommentsViewHandler):
    def get_object(self, username, permalink, type):
        activities = UserActivity.objects.public().filter(film_permalink=permalink, username=username, activity_type=UserActivity.TYPE_RATING)
        if not activities:
            raise Http404 
        return activities[0]

class ActivityCommentsHandler(AnonBaseCommentsViewHandler):
    def get_object(self, username, id):
        return get_object_or_404(UserActivity, username=username, id=id)

class AnonUserFilmShortReviewHandler(AnonymousBaseHandler):
    model = ShortReview
    fields = (
        'review_text', 'resource_uri', 'user_uri', 'film_uri',
        'comments_uri', 'created_at', 'updated_at')

    @classmethod
    def film(self, review):
        return review.object.film
        
    @uri
    def film_uri(self, review):
        if review.object_id:
            return film_handler, [review.object.permalink]

    @uri
    def user_uri(self, review):
        return user_handler, [review.user.username]

    @classmethod
    def author_ratings(self, review):
        return get_rating_list(review.object.film, review.user_id)

    @classmethod
    def author_rating(self, review):
        return get_film_rating(review.object.film, review.user_id)

    @uri
    def resource_uri(self, review):
        return user_wallpost_handler, [review.user.username, review.id]
    
    @uri
    def comments_uri(self, review):
        return user_wallpost_comments_handler, [review.user.username, review.id]

    @user_view
    def read(self, request, username=None, permalink=None):
        objects = ShortReview.objects.filter(
            user__username=username,
            object__permalink=permalink,
            object__type=Object.TYPE_FILM
        ).order_by('-created_at')[0:1]
        if not objects:
            raise Http404
        return objects[0]
    
class UserFilmShortReviewHandler(AnonUserFilmShortReviewHandler):
    is_anonymous = False
    allowed_methods = ('GET', 'PUT', 'DELETE')
    anonymous = AnonUserFilmShortReviewHandler
    
    @user_view_rw
    def delete(self, request, username, permalink):
        review = self.read(request, username, permalink)
        review.delete()
        return review

    @user_view_rw
    def update(self, request, username, permalink):
        form = ShortReviewForm(request.data)
        if not form.is_valid():
            logger.error('for is not valid')
            return BAD_REQUEST(form_errors(form))
        review_text = form.cleaned_data['review_text']        
        try:
            review = self.read(request, username, permalink)
            review.review_text = review_text
            review.save()
        except Http404:
            film = get_object_or_404(Film, permalink=permalink)
            user = get_user(request, username)
            review = ShortReview.objects.create(
                kind=ShortReview.REVIEW,
                user=user,
                object=film,
                review_text=review_text,
                type=ShortReview.TYPE_SHORT_REVIEW,
            )
        return review

def _wrap_related(name, username, id, type, obj):
    return {
        ('%s_uri'%name):reverse(film_handler, args=[obj.permalink]),
        name:obj,
        'resource_uri':reverse(user_post_related_handler, args=[username, id, type, obj.permalink]),
    }

class AnonUserPostRelatedHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username, id, type, related_permalink=None):
        post = get_object_or_404(Post, id=id)
        if type=='films':
            name, collection = 'film', post.related_film
        elif type=='persons':
            name, collection = 'person', post.related_person
        else:
            return BAD_REQUEST(_(u"invalid filter: %s"%type))
        if related_permalink:
            obj = get_object_or_404(collection, permalink=related_permalink)
            return _wrap_related(name, username, id, type, obj)
        return paginated_collection(request, collection.all(), lambda x:_wrap_related(name, username, id, type, x))
        
class UserPostRelatedHandler(AnonUserPostRelatedHandler):
    is_anonymous=False
    anonymous = AnonUserPostRelatedHandler
    allowed_methods = ('GET', 'POST', 'DELETE')
    
    @user_view_rw
    def create(self, request, username, id, type):
        post = get_object_or_404(Post, id=id)
        if request.user.username!=username or post.user.username != username:
            return rc.FORBIDDEN
        data = request.data
        if type=='films':
            name, collection = 'film', post.related_film
        elif type=='persons':
            name, collection = 'person', post.related_person
        else:
            return BAD_REQUEST(_(u"invalid filter: %s"%type))
            
        obj = get_resource(request, data.get(name+"_uri"))
        if not obj: 
            return BAD_REQUEST(_(u"%s_uri is required"%name))
        collection.add(obj)
        post.save_activity()
        return _wrap_related(name, username, id, type, obj)

    @user_view_rw
    def delete(self, request, username, id, type, related_permalink):
        post = get_object_or_404(Post, id=id)
        if request.user.username!=username or post.user.username != username:
            return rc.FORBIDDEN
        if type=='films':
            name, cls, collection = 'film', Film, post.related_film
        elif type=='persons':
            name, cls, collection = 'person', Person, post.related_person
        else:
            return BAD_REQUEST(_(u"invalid filter: %s"%type))
        obj = get_object_or_404(cls, permalink=related_permalink)
        collection.remove(obj)
        post.save_activity()
        return _wrap_related(name, username, id, type, obj)

def filter_posts(request, posts):
    q = Q(status=Post.PUBLIC_STATUS)
    if request.user.is_authenticated() and request.user.username == request.username:
        q = q | Q(status=Post.DRAFT_STATUS)
    return posts.filter(q)
    
class AnonUserPostHandler(AnonymousBaseHandler):
    model = Post
    fields = ('status', 'title', 'lead', 'body', 'is_published', 'spoilers', 'permalink',
              'created_at', 'updated_at', 'resource_uri', 'comments_uri',
              'related_films_uri', 'related_persons_uri', 'user_uri')
    include_fields = ('user', 'author_rating', 'author_ratings')
    
    @user_view
    def read(self, request, username, id=None):
        if not id: 
            return self.read_posts(request, username)
        return get_object_or_404(Post, id=id)
    
    def read_posts(self, request, username):
        posts = Post.objects.filter(user__username=username).order_by('-created_at')
        posts = filter_posts(request, posts)
        posts = posts.select_related('user')
        return paginated_collection(request, posts)
    
    @uri
    def user_uri(self, post):
        return user_handler, [post.user.username]
    
    @classmethod
    def user(self, post):
        return post.user
    
    @uri
    def resource_uri(self, post):
        return user_post_handler, [post.user.username, post.id]
    
    @uri
    def comments_uri(self, post):
        return user_post_comments_handler, [post.user.username, post.id]
    
    @uri
    def related_films_uri(self, post):
        return user_post_related_handler, [post.user.username, post.id, 'films']

    @uri
    def related_persons_uri(self, post):
        return user_post_related_handler, [post.user.username, post.id, 'persons']
    
    @classmethod
    def lead(cls, post):
        return strip_html(post.lead)

    @classmethod
    def body(cls, post):
        return strip_html(post.body)

    @classmethod
    def author_ratings(self, post):
        try:
            film = post.related_film.get()
            return get_rating_list(film, post.user_id) or []
        except (Film.MultipleObjectsReturned, Film.DoesNotExist):
            return []

    @classmethod
    def author_rating(self, post):
        try:
            film = post.related_film.get()
            return get_film_rating(film, post.user_id)
        except (Film.MultipleObjectsReturned, Film.DoesNotExist):
            pass
    
class UserPostHandler(AnonUserPostHandler):
    is_anonymous = False
    anonymous = AnonUserPostHandler
    allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')

    def create_or_update(self, request, username, id=None):
        instance = id and self.read(request, username, id) or None
        
        req_data = request.data
        data = instance and model_to_dict(instance) or {}
        data.update(req_data.items())
    
        form = BlogPostForm(request.user, data, instance=instance)
        if not form.is_valid():
            return BAD_REQUEST(form_errors(form))
        post = form.save(commit=False)
        if not instance:
            post.type = Object.TYPE_POST
            post.user = request.user
        if not instance or not post.is_public:
            post.permalink = slughifi(post.title)            
        if not instance and not 'status' in req_data:
            post.status = Post.DRAFT_STATUS
        if 'status' in request.data:
            post.status = int(req_data.get('status'))
        post.save()
        return post
    
    @user_view_rw
    def update(self, request, username, id):
        return self.create_or_update(request, username, id)
        
    @user_view_rw
    def create(self, request, username):
        return self.create_or_update(request, username)
    
    @user_view_rw
    def delete(self, request, username, id):
        post = self.read(request, username, id)
        post.status = Post.DELETED_STATUS
        post.save()
        return post

class MessageHandler(BaseHandler):
    model = Message
    fields = ('resource_uri', 'recipient_uri', 'sender_uri', 'subject', 'body', 
              'date', 'read_at', 'is_read', 'parent_uri', 'conversation_uri')

    allowed_methods = ('GET', 'POST', 'DELETE')
    
    def read(self, request, id=None, filter='inbox', mark_as_read=True):
        def _read():
            if id is None:
                if filter == 'outbox':
                    meth = Message.objects.outbox_for
                elif filter == 'trash':
                    meth = Message.objects.trash_for
                else:
                    meth = Message.objects.inbox_for
                msgs = meth(request.user).select_related('recipient', 'sender')
                return paginated_collection(request, msgs)
                
            logging.info('mark_as_read: %s', mark_as_read)
            msg = get_object_or_404(Message, pk=id)
            if request.user.pk not in (msg.recipient_id, msg.sender_id):
                return rc.FORBIDDEN
                
            if not msg.read_at and mark_as_read and request.user.pk == msg.recipient_id:
                msg.mark_as_read()
            return msg

        # TODO: check if is this necessary?
        # read is called in create (by get_resource), and we dont want nested
        # commit_on_success calls, so:
#        if mark_as_read:
#            return transaction.commit_on_success(_read)()
#        else:
#            return _read()
        return _read()
    
#    @transaction.commit_on_success
    def create(self, request):
        data = request.data
        subject = data.get('subject', '')
        body = data.get('body', '')
        recipient_uri = data.get('recipient_uri')
        if not recipient_uri:
            return BAD_REQUEST(_("recipient_uri is required"))
        recipient = get_resource(request, recipient_uri)        
        parent = get_resource(request, data.get('parent_uri'), mark_as_read=False)

        messages = Message.send(request.user, [recipient], subject, body, parent_msg=parent)
        return messages[0]

#    @transaction.commit_on_success
    def delete(self, request, id):
        msg = self.read(request, id)
        msg.delete_by(request.user)
        return msg
    
    @uri
    def recipient_uri(cls, message):
        return user_handler, [message.recipient.username]

    @uri
    def sender_uri(cls, message):
        return user_handler, [message.sender.username]
    
    @classmethod
    def date(cls, message):
        return message.sent_at
    
    @classmethod
    def read_at(cls, message):
        request = get_request()
        return message.read_at if request.user.pk == message.recipient_id else message.sent_at
    
    @classmethod
    def is_read(cls, message):
        return bool(cls.read_at(message))
    
    @uri
    def resource_uri(cls, message):
        return message_handler, [message.pk]
    
    @uri
    def parent_uri(cls, message):
        return message.parent_msg_id and (message_handler, [message.parent_msg_id])
    
    @uri
    def conversation_uri(cls, message):
        return message.conversation_id and (conversation_handler, [message.conversation_id])

class ConversationHandler(BaseHandler):
    model = Conversation
    allowed_methods = ('GET', 'DELETE')
    fields = ('subject', 'body', 'created_at', 'updated_at', 'sender_uri', 'resource_uri', 'unread_cnt', 'message_cnt', 'messages_uri')
    
    def read(self, request, id=None):
        if id:
            c = get_object_or_404(Conversation, id=id)
            if request.user.pk not in (c.sender_id, c.recipient_id):
                return rc.FORBIDDEN
            return c
        return paginated_collection(request, Conversation.objects.user_conversations(request.user))

#    @transaction.commit_on_success
    def delete(self, request, id):
        c = get_object_or_404(Conversation, id=id)
        if request.user.pk not in (c.sender_id, c.recipient_id):
            return rc.FORBIDDEN
        c.delete_by(request.user)
        return c
    
    @uri
    def resource_uri(self, c):
        return conversation_handler, [str(c.pk)]
    
    @classmethod
    def message_cnt(self, c):
        request = get_request()
        if request.user.pk == c.sender_id:
            return c.sender_cnt
        if request.user.pk == c.recipient_id:
            return c.recipient_cnt
        assert False, "%s isn't conversation sender nor recipient" % request.user
    
    @classmethod
    def unread_cnt(self, c):
        request = get_request()
        if request.user.pk == c.sender_id:
            return c.sender_unread_cnt
        if request.user.pk == c.recipient_id:
            return c.recipient_unread_cnt
        assert False, "%s isn't conversation sender nor recipient" % request.user
    
    @classmethod
    def sender(self, c):
        request = get_request()
        peer = c.sender_id == request.user.pk and c.recipient or c.sender
        return peer
    
    @uri
    def sender_uri(self, c):
        request = get_request()
        peer = c.sender_id == request.user.pk and c.recipient or c.sender
        return user_handler, [peer.username]
    
    @uri
    def messages_uri(self, c):
        return conversation_messages_handler, [c.pk]

class ConversationMessagesHandler(BaseHandler):
    def read(self, request, id):
        c = get_object_or_404(Conversation, id=id)
        if request.user.pk not in (c.sender_id, c.recipient_id):
            return rc.FORBIDDEN
        threaded = 'threaded' in request.GET
        if not threaded:
            return paginated_collection(request, c.user_messages(request.user))
        else:
            return paginated_collection(request, c.threaded_messages(request.user))

def _get_activities(request, username=None, filter=None):
        P = lambda name: request.GET.get(name) is not None


        reviews = P('reviews') or P('posts') or filter == 'posts'
        shorts = P('shorts') or P('short_reviews') or filter == 'short_reviews'
        comments = P('comments') or filter == 'comments'
        links = P('links') or filter == 'links'
        follows = P('follows') or filter == 'follows'
        checkins = P('checkins') or filter == 'checkins'
        ratings = P('ratings') or filter == 'ratings'

        following = P('comrades') | P('following')
        similar = P('similar-taste')

        most_interesting_reviews = P('interesting')
        favorites = P('favorites')
        
        activities = UserActivity.objects.public()
        
        if username:
            activities = activities.filter(username=username)
        
        types = ()
        if reviews:
            types += (UserActivity.TYPE_POST, )
        if shorts:
            types += (UserActivity.TYPE_SHORT_REVIEW, )
        if comments:
            types += (UserActivity.TYPE_COMMENT, )
        if links: 
            types += (UserActivity.TYPE_LINK, )
        if checkins: 
            types += (UserActivity.TYPE_CHECKIN, )
        if follows:
            types += (UserActivity.TYPE_FOLLOW, )
        if ratings:
            types += (UserActivity.TYPE_RATING, )
        if types:
            activities = activities.filter(activity_type__in=types)

        if request.user.is_authenticated() and (following or similar):
            activities = activities.users(request.user, following=following, similar=similar)
            
        if most_interesting_reviews:
            activities = activities.interesting()

        tags = request.GET.get('tags')
        if tags:
            activities = activities.film_tagged(tags)
        
        film_uri = request.GET.get('film_uri')
        if film_uri:
            activities = activities.filter(film=get_resource(request, film_uri))

        person_uri = request.GET.get('person_uri')
        if person_uri:
            activities = activities.filter(person=get_resource(request, person_uri))

        activities = activities.order_by('-created_at')
        return activities

class AnonUserActivityHandler(AnonymousBaseHandler):
    model = UserActivity
    fields = ('object_uri', 'user_uri', 'author_rating', 'follower_uri', 'type', 'title', 'content', 'created_at', 'modified_at', 'resource_uri', 'film_permalink', 'film_title', 'number_of_comments', 'url', 'url_kind', 'comments_uri')

    ACTIVITY_TYPE_MAP = {
      'short_reviews': UserActivity.TYPE_SHORT_REVIEW,      
      'posts': UserActivity.TYPE_POST,      
      'comments': UserActivity.TYPE_COMMENT,
      'links': UserActivity.TYPE_LINK,
      'follows': UserActivity.TYPE_FOLLOW,
    }

    @user_view
    def read(self, request, username, filter=None, id=None):
        if id:
            return get_object_or_404(UserActivity, user__username=username, pk=id)
        activities = _get_activities(request, username=username, filter=filter)
        return paginated_collection(request, activities)

    @uri
    def resource_uri(cls, activity):
        return user_activity_handler, [activity.username, activity.id]
    
    @uri
    def user_uri(cls, activity):
        return user_handler, [activity.username]
        
    @uri
    def follower_uri(cls, activity):
        if activity.activity_type == UserActivity.TYPE_FOLLOW:
            parsed = activity.content.split(' ')
            return user_handler, [parsed[2]]
            
    @classmethod
    def user(cls, activity):
        return activity.user
    
    @classmethod
    def follower(cls, activity):
        if activity.activity_type == UserActivity.TYPE_FOLLOW:
            parsed = activity.content.split(' ')
            return User.objects.get(username=parsed[2])
    
    @classmethod
    def type(cls, activity):
        return activity.activity_type
    
    @classmethod
    def content(cls, activity):
        return strip_html(activity.content)
        
    @uri
    def post_uri(cls, activity):
        return activity.post_id and (user_post_handler, [activity.username, activity.post_id])

    @uri
    def short_review_uri(cls, activity):
        return activity.short_review_id and (user_wallpost_handler, [activity.username, activity.short_review_id])
    
    @uri
    def comment_uri(cls, activity):
        return activity.comment_id and (comment_handler, [activity.comment_id])
    
    @uri
    def link_uri(cls, activity):
        return activity.link_id and (external_link_handler, [activity.link_id])
    
    @uri
    def checkin_uri(cls, activity):
        return activity.checkin_id and (checkin_handler, [activity.checkin_id])

    @uri
    def rating_uri(cls, activity):
        return activity.activity_type == activity.TYPE_RATING and (film_rating_handler, [activity.username, activity.film_permalink, Rating.TYPE_FILM])
    
    @classmethod
    def object_uri(cls, activity):
        TYPE_URI = {
          UserActivity.TYPE_POST: cls.post_uri,
          UserActivity.TYPE_SHORT_REVIEW: cls.short_review_uri,
          UserActivity.TYPE_COMMENT: cls.comment_uri,
          UserActivity.TYPE_LINK: cls.link_uri,
          UserActivity.TYPE_CHECKIN: cls.checkin_uri,
          UserActivity.TYPE_RATING: cls.rating_uri,
        }
        cb = TYPE_URI.get(activity.activity_type)
        if cb:
            return cb(activity)
    
    @classmethod
    def comments_uri(cls, activity):
        return cls.resource_uri(activity) + 'comments/'

    @classmethod
    def author_rating(cls, activity):
        # TODO - store and use rating from activity.rating
        if activity.film:
            return get_film_rating(activity.film, activity.user_id)

class UserActivityHandler(AnonUserActivityHandler):
    anonymous = AnonUserActivityHandler
    is_anonymous = False

class FilmActivityHandler(AnonymousBaseHandler):
    def read(self, request, permalink):
        q = Q(post__related_film__permalink=permalink) | Q(short_review__object__permalink=permalink)
        activities = UserActivity.objects.select_related('user','post','short_review','film')\
                                  .filter(q, object__status=Object.PUBLIC_STATUS)\
                                  .order_by("-created_at")
        return paginated_collection(request, activities)

class FilmPostsHandler(BaseHandler):
    def read(self, request, permalink):
        film = get_object_or_404(Film, permalink=permalink)
        # TODO - nonsence m2m related_name, rename to related_posts
        posts = film.related_film.filter(status=Post.PUBLIC_STATUS)
        return paginated_collection(request, posts)

class PersonPostsHandler(BaseHandler):
    def read(self, request, permalink):
        person = get_object_or_404(Person, permalink=permalink)
        # TODO - nonsence m2m related_name, rename to related_posts
        posts = person.related_people.all()
        return paginated_collection(request, posts)

class PlanetHandler(AnonymousBaseHandler):
    def read(self, request):
        return paginated_collection(request, _get_activities(request))

class TownHandler(AnonymousBaseHandler):
    model = Town
    fields = ("name", "country_code", "cinema_uri", "cinema_showtimes_uri", "showtimes_uri", "resource_uri")

    def read(self, request, id):
        collection = Town.objects_with_cinemas.select_related('country')
        festival = get_festival(request)
        if festival:
            channels = festival.get_theaters()
            collection = collection.filter(channel__town__in=[c.town_id for c in channels])
        if not id.isdigit():
            collection = collection.filter(country__code=id.upper())
            return paginated_collection(request, collection)
        return get_object_or_404(collection, pk=id)
    
    @uri
    def resource_uri(cls, town):
        return town_handler, [town.pk]
    
    @classmethod
    def country_code(cls, town):
        return town.country.code

    @uri
    def showtimes_uri(cls, town):
        return town_showtimes_handler, [town.pk]
    
    @uri
    def cinema_uri(cls, town):
        return town_cinema_handler, [town.pk]

    @uri
    def cinema_showtimes_uri(cls, town):
        return town_cinema_showtimes_handler, [town.pk]

class CountryHandler(AnonymousBaseHandler):
    model = Country
    fields = ("name", "code", "towns_uri", "resource_uri", "tvchannels_uri", "festival_uri")

    def read(self, request, id=None):
        collection = Country.objects.all()
        if not id:
            return paginated_collection(request, collection)
        return get_object_or_404(collection, code=id.upper())
    
    @uri
    def resource_uri(cls, country):
        return country_handler, [country.code]
    
    @uri
    def towns_uri(cls, country):
        return town_handler, [country.code]

    @uri
    def tvchannels_uri(cls, country):
        return country_tvchannel_handler, [country.code]
        
    @uri
    def festival_uri(cls, country):
        return country_festival_handler, [country.code]
    
#class CinemaHandler(AnonymousBaseHandler):
#    model = Cinema
#    fields = ("name", "address", "latitude", "longitude", "town_uri")
#    
#    def read(self, request, id):
#        return get_object_or_404(Cinema, id=id)

class ScreeningHandler(AnonymousBaseHandler):
    model = Screening
    fields = ("time", "resource_uri")
    
    @uri
    def resource_uri(cls, scr):
        return screening_handler, [scr.id]
    
    @classmethod
    def checked_in_cnt(cls, scr):
        return scr.checkin_cnt()
    
    @classmethod
    def auth_checked_in(cls, scr):
        request = get_request()
        if request.user.is_authenticated():
            return any(s.user_id == request.user.pk for s in scr.get_checkins())

    @classmethod
    def checked_in(cls, scr):
        request = get_request()
        username = getattr(request, 'username', None)
        if username:
            return any(s.user.username == username for s in scr.get_checkins())
    
    @classmethod
    def time(cls, scr):
        request = get_request()
        return scr.get_local_time(request.timezone)
    
class FilmScreeningsChannelHandler(AnonymousBaseHandler):
    model = FilmScreeningsChannel
    fields = ("channel_uri", "screenings")

    @uri
    def channel_uri(cls, obj):
        return channel_handler, [obj.channel.pk]

class ChannelScreeningsFilmHandler(AnonymousBaseHandler):
    model = ChannelScreeningsFilm
    fields = ("screenings", "film", "film_uri", "film_title")

    @uri
    def film_uri(cls, film):
        return film_handler, [film.film.permalink]

    @classmethod
    def film_title(cls, film):
        return film.film.title
    
    @classmethod
    def film(cls, film):
        return film.film

def get_available_showtimes(request, view, username=None, town_id=None, channel=None, festival=None):
    id = username or town_id or channel and channel.id
    user = username and get_object_or_404(User, username=username)
    town = town_id and get_object_or_404(Town.objects_with_cinemas, pk=town_id)
    dates = get_available_showtime_dates(request)
    if festival:
        if not 'with_past' in request.GET:
            dates = filter(lambda d:dates and d>=dates[0], festival.get_screening_dates())
        else:
            dates = festival.get_screening_dates()
    return collection(request, ({
        'date':d.date(),
        'resource_uri':reverse(view, args=[id, str(d.date())]),
    } for d in dates))

def channel_type(request):
    try:
        return int(request.GET.get('type', 1))
    except ValueError:
        return 1

def _showtimes_filter(request):
    with_rated = 'with_rated' in request.GET
    without_unmatched = 'without_unmatched' in request.GET
    past = 'with_past' in request.GET
    order_by = request.GET.get('order')
    tags = request.GET.get('tags')
    
    if channel_type(request) == 2:
        without_unmatched = True
        
    return dict(
        tags=tags,
        with_rated=with_rated,
        without_unmatched=without_unmatched,
        past=past,
        order_by=order_by,
    )

def get_festival(request):
    if 'tags' in request.GET:
        festival = Festival.objects.filter(tag__iexact=request.GET.get('tags'))
        return festival and festival[0] or None

class UserShowtimesHandler(AnonymousBaseHandler):
    model = FilmScreenings
    fields = ("film_uri", "channels", "film_title")
    
    @user_view
    def read(self, request, username, date=None):
        festival = get_festival(request)
        if not date:
            return get_available_showtimes(request, user_showtimes_handler, username=username, festival=festival)
        try:
            date = parse_date(request, date)
        except ValueError, e:
            return BAD_REQUEST(unicode(e))
        user = get_user(request, username)
        if festival:
            channels = festival.get_theaters()
        else:
            channels = Channel.objects.selected_by(user, channel_type(request))
        channels = sort_channels(request, channels)
        films = ScreeningSet(date, channels, user, **_showtimes_filter(request)).get_recommendations()
        return paginated_collection(request, [ FilmScreenings(film=film) for film in films ])
        
    @uri
    def film_uri(cls, film):
        return film_handler, [film.film.permalink]

    @classmethod
    def film_title(cls, film):
        return film.film.title
    
    @classmethod
    def film(cls, film):
        return film.film

def selected_channels(request):
    if not hasattr(request, "_user_channels"):
        if request.user.is_authenticated():
            channels = Channel.objects.selected_by(request.user, Channel.TYPE_TV_CHANNEL | Channel.TYPE_CINEMA)
            request._user_channels = sort_channels(request, channels)
        else:
            request._user_channels = ()
    return request._user_channels

class ChannelHandler(AnonymousBaseHandler):
    model = Channel
    fields = ("latitude", "longitude", "name", "address", "type", "town_uri", "resource_uri", "distance")
    
    @classmethod
    def latitude(cls, channel):
        return channel.latitude

    @classmethod
    def longitude(cls, channel):
        return channel.longitude

    @classmethod
    def address(cls, channel):
        return channel.address
    
    @uri
    def resource_uri(cls, channel):
        return (channel_handler, [channel.pk])
    
    @classmethod
    def distance(cls, channel):
        return channel.distance
    
    @classmethod
    def is_selected(cls, channel):
        request = get_request()   
        channels = selected_channels(request)
        return channel in channels
    
    @uri
    def town_uri(cls, channel):
        if channel.town_id:
            return town_handler, [channel.town_id]

class OldUserChannelHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username):
        user = get_user(request, username)
        channels = Channel.objects.selected_by(user, channel_type(request))
        channels = sort_channels(request, channels)
        return paginated_collection(request, channels)

class UserChannelHandler(AnonymousBaseHandler):
    model = UserChannel
    fields = ('channel_uri', 'distance', 'channel')
    allowed_methods = ('GET', 'POST', 'DELETE')
    
    @user_view
    def read(self, request, username, id=None):
        user = get_user(request, username)
        try:
            type = int(request.GET.get('type', 3))
        except ValueError, e:
            type = 3

        type_q = Q()
        for mask in (1, 2):
            if type & mask:
                type_q = type_q | Q(channel__type=mask)
            
        if id is None:
            channels = UserChannel.objects.filter(user=user).filter(type_q)
            channels = channels.select_related('user', 'channel')
            channels = channels.order_by('channel__type', 'distance', 'channel__name')
            channels = sort_channels(request, channels)
            return paginated_collection(request, channels)
        
        return get_object_or_404(UserChannel, user=user, channel__id=id)
    
    @user_view_rw
    def delete(self, request, username, id):
        item = get_object_or_404(UserChannel, user__username=username, channel__id=id)
        item.delete()
        return item
    
    @user_view_rw
    def create(self, request, username):
        user = get_user(request, username)
        channel_uri = request.data.get('channel_uri')
        if not channel_uri:
            return BAD_REQUEST("channel_uri is required")
        channel = get_resource(request, channel_uri)
        logger.info("%r %r %r", user, channel_uri, channel)
        c, created = UserChannel.objects.get_or_create(user=user, channel=channel)
        return c
    
    @uri
    def channel_uri(cls, channel):
        return (channel_handler, [channel.channel_id])
        
    @uri
    def resource_uri(cls, channel):
        return user_channel_handler, [channel.user.username, channel.channel_id]
    
class UserChannelShowtimesHandler(AnonymousBaseHandler):
    model = ChannelScreenings
    fields = ("channel_uri", "films")
    
    @user_view
    def read(self, request, username, date=None):
        festival = get_festival(request)
        if not date:
            return get_available_showtimes(request, user_channel_showtimes_handler, username=username, festival=festival)
        try:
            date = parse_date(request, date)
        except ValueError, e:
            return BAD_REQUEST(unicode(e))
        user = get_user(request, username)
        if festival:
            channels = festival.get_theaters()
        else:
            channels = Channel.objects.selected_by(user, channel_type(request))
        channels = sort_channels(request, channels)

        screening_set = ScreeningSet(date, channels, user, **_showtimes_filter(request))
        ch = screening_set.get_recommendations_by_channel()
        channel_screenings = [ChannelScreenings(channel=c) for c in ch]
        return paginated_collection(request, channel_screenings)
        
    @uri
    def channel_uri(cls, obj):
        return (channel_handler, [obj.channel.pk])

class ChannelShowtimesHandler(AnonymousBaseHandler):
    def read(self, request, id, date=None):
        channel = get_object_or_404(Channel, id=id)
        if not date:
            return get_available_showtimes(request, channel_showtimes_handler, channel=channel)
        try:
            date = parse_date(request, date)
        except ValueError, e:
            return BAD_REQUEST(unicode(e))
        
        screening_set = ScreeningSet(date, [channel], **_showtimes_filter(request))
        films = screening_set.get_recommendations()[:] # recommendations for single channel

        return collection(request, (ChannelScreeningsFilm(film=f, screenings=f.screenings) for f in films))
        
class TownShowtimesHandler(AnonymousBaseHandler):
    def read(self, request, id, date=None):
        festival = get_festival(request)
        if not date:
            return get_available_showtimes(request, town_showtimes_handler, town_id=id, festival=festival)
        try:
            date = parse_date(request, date)
        except ValueError, e:
            return BAD_REQUEST(unicode(e))
        town = get_object_or_404(Town.objects_with_cinemas, pk=id)
        channels = Channel.objects.in_town(town)
        channels = sort_channels(request, channels)

        films = ScreeningSet(date, channels, request.user, **_showtimes_filter(request)).get_recommendations()
        return paginated_collection(request, [ FilmScreenings(film=film) for film in films ])
        
    @uri
    def film_uri(cls, film):
        return film_handler, [film.film.permalink]

class TownCinemaShowtimesHandler(AnonymousBaseHandler):
    def read(self, request, id, date=None):
        festival = get_festival(request)
        if not date:
            return get_available_showtimes(request, town_cinema_showtimes_handler, town_id=id, festival=festival)
        user = request.user        
        try:
            date = parse_date(request, date)
        except ValueError, e:
            return BAD_REQUEST(unicode(e))
        town = get_object_or_404(Town.objects_with_cinemas, pk=id)
        channels = Channel.objects.in_town(town)
        channels = sort_channels(request, channels)
        
        screening_set = ScreeningSet(date, channels, user, **_showtimes_filter(request))
        ch = screening_set.get_recommendations_by_channel()
        channel_screenings = [ChannelScreenings(channel=c) for c in ch]
        return paginated_collection(request, channel_screenings)

        
    @uri
    def film_uri(cls, film):
        return film_handler, [film.film.permalink]

class TownCinemaHandler(AnonymousBaseHandler):
    def read(self, request, id):
        town = get_object_or_404(Town.objects_with_cinemas, pk=id)
        channels = Channel.objects.in_town(town)
        festival = get_festival(request)
        if festival:
            channels = filter(lambda t:t.id in [c.id for c in festival.get_theaters()], channels)
        
        return paginated_collection(request, channels)

class CountryTVChannelHandler(AnonymousBaseHandler):
    def read(self, request, code):
        country = get_object_or_404(Country, code=code.upper())
        query_string = request.GET.get('q', '')
        channels = Channel.objects.tv().filter(country=country, is_active=True)
        if query_string:
            channels = channels.filter(name__istartswith=query_string)
        channels = sort_channels(request, channels)
        return paginated_collection(request, channels)

class AnonCheckinHandler(AnonymousBaseHandler):
    model = ScreeningCheckIn
    fields = ('user_uri', 'screening_uri', 'created_at', 'resource_uri', 'film_uri')
    
    def read(self, request, id=None):
        objects = ScreeningCheckIn.objects.select_related().order_by('-created_at')
        if id:
            return get_object_or_404(objects, id=id)
        return paginated_collection(request, objects)

    @uri
    def resource_uri(cls, checkin):
        return checkin_handler, [checkin.id]
    
    @uri
    def screening_uri(cls, checkin):
        return checkin.screening_id and (screening_handler, [checkin.screening_id]) or None
        
    @uri
    def user_uri(cls, checkin):
        return user_handler, [checkin.user.username]
    
    @uri
    def film_uri(cls, checkin):
        return checkin.film_id and (film_handler, [checkin.film.permalink]) or None
    
    @classmethod
    def avatar(cls, checkin):
        return UserHandler.avatar(checkin.user)

    @uri
    def comments_uri(self, checkin):
        return checkin_comments_handler, [checkin.id]

class CheckinHandler(AnonCheckinHandler):
    is_anonymous = False
    anonymous = AnonCheckinHandler
    allowed_methods = ('GET', 'DELETE', 'POST')
    
    def delete(self, request, id):
        checkin = get_object_or_404(ScreeningCheckIn.objects.select_related(), id=id)
        if request.user != checkin.user:
            return rc.FORBIDDEN
        checkin.status = ScreeningCheckIn.CANCELED
        checkin.save()
        return checkin

    def create(self, request):
        user_uri = request.data and request.data.get('user_uri')
        if user_uri:
            user = get_resource(request, user_uri)
        else:
            user = request.user
        if user != request.user:
            logger.warning("%r %r", user, request.user)
            return rc.FORBIDDEN
        screening_uri = request.data.get('screening_uri')
        film_uri = request.data.get('film_uri')
        screening = screening_uri and get_resource(request, screening_uri)
        film = film_uri and get_resource(request, film_uri)
        logger.info("%r %r", screening, film)
        if not screening and not film or screening and film:
            return BAD_REQUEST("provide film_uri or screening_uri (not both)")
        if screening:
            return screening.check_in(user)
        else:
            return film.check_in(user)

class AnonScreeningCheckinHandler(AnonymousBaseHandler):
    def read(self, request, id, username=None):
        if username is None:
            return paginated_collection(request, 
                                        ScreeningCheckIn.objects.filter(screening__id=id).order_by('created_at').select_related())
        return get_object_or_404(ScreeningCheckIn.objects.select_related(),
                                 screening__id=id, user__username=username)

class AnonFilmCheckinHandler(AnonymousBaseHandler):
    def read(self, request, permalink, username=None):
        if username is None:
            return paginated_collection(request,
                                        ScreeningCheckIn.objects.filter(film__permalink=permalink).order_by('created_at').select_related())
        return get_object_or_404(ScreeningCheckIn.objects.select_related(),
                                 film__permalink=permalink, user__username=username)

class AnonUserCheckinHandler(AnonymousBaseHandler):
    def read(self, request, username):
        objects = ScreeningCheckIn.objects.filter(user__username=username).order_by('-created_at')
        return paginated_collection(request, objects.select_related())

# TODO - remove in next api version (CheckinHandler is writable now)
class ScreeningCheckinHandler(AnonScreeningCheckinHandler):
    is_anonymous = False
    anonymous = AnonScreeningCheckinHandler
    allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')
    
    def create(self, request, id):
        screening = get_object_or_404(Screening, id=id)
        user_uri = request.data and request.data.get('user_uri')
        if user_uri:
            user = get_resource(request, user_uri)
        else:
            user = request.user
        if user != request.user:
            logger.warning("%r %r", user, request.user)
            return rc.FORBIDDEN
        return screening.check_in(request.user)
    
    def update(self, request, id, username):
        if request.user.username != username:
            return rc.FORBIDDEN
        screening = get_object_or_404(Screening, id=id)
        return screening.check_in(request.user)
        
    def delete(self, request, id, username):
        if request.user.username != username:
            return rc.FORBIDDEN
        screening = get_object_or_404(Screening, id=id)
        return screening.check_in_cancel(request.user)

class FilmCheckinHandler(AnonFilmCheckinHandler):
    is_anonymous = False
    anonymous = AnonFilmCheckinHandler
    allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')

    def create(self, request, permalink):
        film = get_object_or_404(Film, permalink=permalink)
        user_uri = request.data and request.data.get('user_uri')
        if user_uri:
            user = get_resource(request, user_uri)
        else:
            user = request.user
        if user != request.user:
            logger.warning("%r %r", user, request.user)
            return rc.FORBIDDEN
        return film.check_in(request.user)

    def update(self, request, permalink, username):
        if request.user.username != username:
            return rc.FORBIDDEN
        film = get_object_or_404(Film, permalink=permalink)
        return film.check_in(request.user)

    def delete(self, request, permalink, username):
        if request.user.username != username:
            return rc.FORBIDDEN
        film = get_object_or_404(Film, permalink=permalink)
        return film.check_in_cancel(request.user)

from film20.festivals.models import Festival

class FestivalHandler(AnonymousBaseHandler):
    model = Festival
    fields = ('name', 'short_name', 'lead', 'body', 'tag', 'supertag', 'start_date', 
              'end_date', 'country_code', 'latitude', 'longitude', 
              'resource_uri', 'recommendations_uri', 
              'background_image', 'menu_header_image', 'menu_icon_image',
              'background_image_lowres', 'menu_header_image_lowres', 'menu_icon_image_lowres',
              'rate_films_image', 'rate_films_image_lowres',
              'suggestions_image', 'suggestions_image_lowres',
              'showtimes_image', 'showtimes_image_lowres',
              'community_image', 'community_image_lowres',
              'stream_image', 'stream_image_lowres',
              'channels',
              )

    @static_image
    def background_image(cls, festival):
        return festival.background_image

    @static_image
    def background_image_lowres(cls, festival):
        return festival.background_image_lowres

    @static_image
    def menu_header_image(cls, festival):
        return festival.menu_header_image

    @static_image
    def menu_header_image_lowres(cls, festival):
        return festival.menu_header_image_lowres

    @static_image
    def menu_icon_image(cls, festival):
        return festival.menu_icon_image

    @static_image
    def menu_icon_image_lowres(cls, festival):
        return festival.menu_icon_image_lowres

    @static_image
    def showtimes_image(cls, festival):
        return festival.showtimes_image

    @static_image
    def showtimes_image_lowres(cls, festival):
        return festival.showtimes_image_lowres

    @static_image
    def rate_films_image(cls, festival):
        return festival.rate_films_image

    @static_image
    def rate_films_image_lowres(cls, festival):
        return festival.rate_films_image_lowres

    @static_image
    def suggestions_image(cls, festival):
        return festival.suggestions_image

    @static_image
    def suggestions_image_lowres(cls, festival):
        return festival.suggestions_image_lowres

    @static_image
    def community_image(cls, festival):
        return festival.community_image

    @static_image
    def community_image_lowres(cls, festival):
        return festival.community_image_lowres

    @static_image
    def stream_image(cls, festival):
        return festival.stream_image

    @static_image
    def stream_image_lowres(cls, festival):
        return festival.stream_image_lowres

    def read(self, request, code, id=None):
        objects = Festival.objects.select_related().order_by('created_at')
        objects = objects.filter(event_status=Festival.STATUS_OPEN)
        objects = objects.filter(supported=True)
        objects = objects.filter(country_code=code.upper())
        if request.user.is_authenticated():
            try:
                distance = int(request.GET.get('distance', 0))
                if distance:
                    profile = request.user.get_profile()
                    objects = objects.nearby(profile.latitude, profile.longitude, distance)
            except ValueError:
                pass
        
        if id:
            return get_object_or_404(objects, id=id)
        return paginated_collection(request, objects)
    
    @uri
    def resource_uri(self, obj):
        return country_festival_handler, [obj.country_code, obj.id]

    @uri
    def recommendations_uri(self, obj):
        return festival_recommendations_handler, [obj.country_code, obj.id]
    
    @classmethod
    def lead(cls, obj):
        return strip_html(obj.lead)

    @classmethod
    def body(cls, obj):
        return strip_html(obj.body)

    @classmethod
    def channels(cls, obj):
        return obj.get_theaters()

class FestivalRecommendationsHandler(AnonymousBaseHandler):
    
    def read(self, request, code, id):
        from film20.showtimes.showtimes_helper import user_recommendations
        from film20.festivals.models import Festival

        festival = FestivalHandler().read(request, code, id)

        screening_set = festival.get_screening_set()
        films = screening_set.wrap_films(festival.get_films())
        recommended_films = user_recommendations(request.user, films)
        return paginated_collection(request, [ FilmScreenings(film=film) for film in recommended_films ])

class AnonymousUserWallPostHandler(AnonymousBaseHandler):
    @user_view
    def read(self, request, username=None, id=None):
        user = get_user(request, username)
        objects = ShortReview.all_objects.filter(user=user)
        if id:
            return get_object_or_404(objects, id=id)
        return paginated_collection(request, objects)

from film20.api.forms import WallPostForm

class UserWallPostHandler(AnonymousUserWallPostHandler):
    allowed_methods = ('GET', 'PUT', 'POST', 'DELETE')
    is_anonymous = False
    anonymous = AnonymousUserWallPostHandler

    @user_view_rw
    def create(self, request, username):
        user = get_user(request, username)
        form = WallPostForm(request.data)
        if form.is_valid():
            review_text = form.cleaned_data['review_text']
        else:
            return BAD_REQUEST()

        object = None
        if 'object_uri' in request.data:
            object = get_resource(request, request.data['object_uri'])
            
        post = ShortReview.all_objects.create(
            kind=ShortReview.WALLPOST,
            user=user,
            object=object,
            review_text=review_text,
            type=ShortReview.TYPE_SHORT_REVIEW,
        )
        return post
    
    @user_view_rw
    def update(self, request, username, id):
        user = get_user(request, username)
        post = get_object_or_404(ShortReview.all_objects, user=user, id=id)
        if 'review_text' in request.data:
            form = WallPostForm(request.data)
            if form.is_valid():
                post.review_text = form.cleaned_data['review_text']
            else:
                return BAD_REQUEST()
        post.save()
        return post
    
    @user_view_rw
    def delete(self, request, username, id):
        user = get_user(request, username)
        post = ShortReview.all_objects.get(user=user, id=id)
        post.delete()
        return post

class UserFilmsSeenHandler(BaseHandler):

    def read(self, request, username):
        return []

    @user_view_rw
    def create(self, request, username):
        from film20.core import rating_helper
        user = get_user(request, username)
        data = request.data
        film_uri = data.get('film_uri')
        if not film_uri:
            return BAD_REQUEST()
        film = get_resource(request, film_uri)
        rating_helper.mark_films_as_seen(user, [film.id])
        return {
                'film_uri': film_uri,
        }

class UserRegisterFBHandler(BaseHandler):
    def read(self, request, username):
        return {}

    @user_view_rw
    def create(self, request, username):
        profile = request.user.get_profile()
        data = request.data
        access_token = data.get('access_token')
        if not access_token:
            return BAD_REQUEST()
        if profile.is_temporary:
            tmp_user_id = request.user.id
            from film20.facebook_connect.views import auto_create_fb_user
            user = auto_create_fb_user(request, access_token)
            assert user.id == tmp_user_id
        else:
            # TODO - assign fb
            # from film20.facebook_connect.views import assign_fb
            # assign_fb(request, access_token)
            # user = request.user
            return BAD_REQUEST("user is already registered")
        return {
                'user_uri': reverse(user_handler, args=[user.username]),
                }

class UserRegisterEmailHandler(BaseHandler):
    def read(self, request, username):
        return {}

    @user_view_rw
    def create(self, request, username):
        profile = request.user.get_profile()
        data = request.data
        email = data.get('email')
        if not email:
            return BAD_REQUEST('email is required')
        if profile.is_temporary:
            # request.user.email = email
            # request.user.save()
            from film20.emailconfirmation.models import EmailAddress
            EmailAddress.objects.add_email(request.user, email, email_registration=True)
        else:
            return BAD_REQUEST("user is already registered")
        return {
        }


class NonCachedResource(Resource):
    @never_cache
    def __call__(self, *args, **kw):
        return super(NonCachedResource, self).__call__(*args, **kw)

user_handler = Resource(UserHandler,AUTHORIZED)
profile_handler = user_handler
user_recommendations_handler = Resource(UserRecommendationsHandler, AUTHORIZED)
user_basketitem_handler = Resource(UserBasketItemHandler, AUTHORIZED)
user_basket_handler = user_basketitem_handler
film_ratings_handler = Resource(FilmRatingsHandler, AUTHORIZED)
film_rating_handler = Resource(FilmRatingHandler, AUTHORIZED)
user_unrated_films_handler = NonCachedResource(UnratedFilmsHandler, AUTHORIZED)
user_short_reviews_handler = Resource(UserFilmShortReviewsHandler, AUTHORIZED)
user_short_review_handler = Resource(UserFilmShortReviewHandler, AUTHORIZED)

user_film_meta_handler = Resource(UserFilmMetaHandler, AUTHORIZED)
user_films_seen_handler = Resource(UserFilmsSeenHandler, AUTHORIZED)

user_register_fb_handler = Resource(UserRegisterFBHandler, AUTHORIZED)
user_register_email_handler = Resource(UserRegisterEmailHandler, AUTHORIZED)


user_post_related_handler = Resource(UserPostRelatedHandler, AUTHORIZED)
user_post_handler = Resource(UserPostHandler, AUTHORIZED)
user_checkin_handler = Resource.register_anonymous(AnonUserCheckinHandler)

user_wallpost_handler = Resource(UserWallPostHandler, AUTHORIZED)

#view comments handlers
user_post_comments_handler = Resource.register_anonymous(UserPostCommentsHandler)
user_wallpost_comments_handler = Resource.register_anonymous(UserWallPostCommentsHandler)
checkin_comments_handler = Resource.register_anonymous(CheckinCommentsHandler)
external_link_comments_handler = Resource.register_anonymous(LinkCommentsHandler)
film_rating_comments_handler = Resource.register_anonymous(RatingCommentsHandler)
user_short_review_comments_handler = Resource.register_anonymous(UserShortReviewCommentsHandler)
activity_comments_handler = Resource.register_anonymous(ActivityCommentsHandler)

comment_handler = Resource(CommentHandler, AUTHORIZED)
message_handler = Resource(MessageHandler, AUTHORIZED)

conversation_handler = Resource(ConversationHandler, AUTHORIZED)
conversation_messages_handler = Resource(ConversationMessagesHandler, AUTHORIZED)

user_activity_handler = Resource(UserActivityHandler, AUTHORIZED)

user_following_handler = Resource(UserFollowingHandler, AUTHORIZED)
user_followers_handler = Resource.register_anonymous(UserFollowersHandler)
user_blocking_handler = Resource(UserBlockingHandler, AUTHORIZED)
user_blockers_handler = Resource.register_anonymous(UserBlockersHandler)
user_friends_handler = Resource.register_anonymous(UserFriendsHandler)

user_community_handler = Resource.register_anonymous(UserCommunityHandler)

user_showtimes_handler = Resource.register_anonymous(UserShowtimesHandler)
user_channel_showtimes_handler = Resource.register_anonymous(UserChannelShowtimesHandler)

film_handler = Resource(FilmHandler, AUTHORIZED)
film_related_handler = Resource.register_anonymous(FilmRelatedHandler)

film_ranking_handler = Resource.register_anonymous(FilmRankingHandler)

films_played_handler = Resource.register_anonymous(FilmsPlayedHandler)
film_links_handler = Resource.register_anonymous(FilmLinksHandler)
film_characters_handler = Resource.register_anonymous(FilmCharactersHandler)
films_directed_handler = Resource.register_anonymous(FilmsDirectedHandler)

person_handler = Resource(PersonHandler, AUTHORIZED)
film_short_reviews_handler = Resource.register_anonymous(FilmShortReviewsHandler)

film_posts_handler = Resource.register_anonymous(FilmPostsHandler)
person_posts_handler = Resource.register_anonymous(PersonPostsHandler)

search_film_handler = Resource.register_anonymous(SearchFilmHandler)
search_person_handler = Resource.register_anonymous(SearchPersonHandler)
search_user_handler = Resource.register_anonymous(SearchUserHandler)
search_town_handler = Resource.register_anonymous(SearchTownHandler)

search_handler = Resource.register_anonymous(SearchHandler)

planet_handler = Resource.register_anonymous(PlanetHandler)

#cinema_handler = Resource.register_anonymous(CinemaHandler)
channel_handler = Resource.register_anonymous(ChannelHandler)
channel_showtimes_handler = Resource.register_anonymous(ChannelShowtimesHandler)

screening_handler = Resource.register_anonymous(ScreeningHandler)

old_user_channel_handler = Resource.register_anonymous(OldUserChannelHandler)
user_channel_handler = Resource.register_anonymous(UserChannelHandler)

screening_checkin_handler = Resource(ScreeningCheckinHandler, AUTHORIZED)
film_checkin_handler = Resource.register_anonymous(FilmCheckinHandler)
checkin_handler = Resource(CheckinHandler, AUTHORIZED)

town_handler = Resource.register_anonymous(TownHandler)
country_handler = Resource.register_anonymous(CountryHandler)

town_cinema_handler = Resource.register_anonymous(TownCinemaHandler)
town_showtimes_handler = Resource.register_anonymous(TownShowtimesHandler)
town_cinema_showtimes_handler = Resource.register_anonymous(TownCinemaShowtimesHandler)

country_tvchannel_handler = Resource.register_anonymous(CountryTVChannelHandler)

film_activity_handler = Resource.register_anonymous(FilmActivityHandler)

external_link_handler = Resource.register_anonymous(ExternalLinkHandler)

#festival_handler = Resource(FestivalHandler, AUTHORIZED)
country_festival_handler = Resource.register_anonymous(FestivalHandler)
festival_recommendations_handler = Resource.register_anonymous(FestivalRecommendationsHandler)

