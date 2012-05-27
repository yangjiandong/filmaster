
from piston.handler import BaseHandler as PistonBaseHandler, TypeMapper
from piston.resource import Resource as PistonResource
from piston.utils import rc
from piston.authentication import NoAuthentication, HttpBasicAuthentication

from django import http
from django.core import signals
from django.core.urlresolvers import reverse as django_reverse, resolve
from django.contrib.auth.models import User
from django.views.decorators.cache import never_cache

from django.shortcuts import get_object_or_404

from film20.core.models import Film
from film20.core import rating_helper
from film20.api.utils import paginated_collection, collection
from film20.utils import cache

from ..models import SaaSUser

import re
import json
import logging
logger = logging.getLogger(__name__)

class BadRequestException(Exception):
    pass

VERSION_PREFIX = "/saas/1.0"

def reverse(view, *args, **kw):
    import urls
    return VERSION_PREFIX + django_reverse(view, urlconf=urls, *args, **kw)

def get_resource(request, resource_uri, **kwargs):
    if resource_uri and resource_uri.startswith(VERSION_PREFIX):
        import urls
        handler, args, kw = resolve(resource_uri[len(VERSION_PREFIX):], urlconf=urls)
        kw.update(kwargs)
        logger.info(handler.handler)
        return handler.handler.read(request, *args, **kw)

def uri(method):
    @classmethod
    def wrapper(cls, obj):
        ret = method(cls, obj)
        return ret and reverse(ret[0], args=ret[1]) or ret
    return wrapper

def auth_func(username=None, password=None):
    try:
        user = SaaSUser.objects.get(username=username)
        if user.check_password(password):
            return user
    except SaaSUser.DoesNotExist, e:
        pass

AUTHORIZED = [HttpBasicAuthentication(auth_func=auth_func)]
ANONYMOUS = [NoAuthentication()]

typemapper = TypeMapper()

class Resource(PistonResource):
    @classmethod
    def register_anonymous(cls, handler):
        authorized = type(handler.__name__ + "Anon", (handler,), {
            'is_anonymous':False,
            'anonymous':handler,
        })
        return cls(authorized, AUTHORIZED)

    @classmethod
    def register(cls, handler):
        return cls(handler, AUTHORIZED)

    @classmethod
    def mapper(cls):
        return typemapper

    def error_handler(self, e, request, meth, em_format):
        if not isinstance(e, http.Http404) and not isinstance(e, BadRequestException):
            # signal exception (for unittest report)
            receivers = signals.got_request_exception.send(sender=self.__class__, request=request)
            logger.exception(e)
        if isinstance(e, BadRequestException):
            out = json.dumps({'status': 'error', 'error_description': unicode(e)})
            return http.HttpResponse(out, status=400)
        return super(Resource, self).error_handler(e, request, meth, em_format)

    @never_cache
    def __call__(self, *args, **kw):
        return super(Resource, self).__call__(*args, **kw)

class BaseHandler(PistonBaseHandler):
    SUCCESS_RESPONSE = {
            'status': 'success'
    }
    @classmethod
    def mapper(cls):
        return typemapper

    @classmethod
    def get_user(cls, request, id):
        # cache !
        return get_object_or_404(User, username="%s-%s" % (request.user.user_prefix, id))

    _imdb_code_cache = {}
    @classmethod
    def film_id_to_imdb_code(cls, film_id):
        imdb_code = cls._imdb_code_cache.get(film_id)
        if imdb_code is None:
            film = Film.get(id=film_id)
            imdb_code = film and film.imdb_code
            if imdb_code:
                cls._imdb_code_cache[film_id] = imdb_code
        return imdb_code

class UsersHandler(BaseHandler):
    model = User
    fields = ('resource_uri', 'id')

    def read(self, request, id=None):
        if not id:
            return BadRequestResponse()
        return self.get_user(request, id)

    @classmethod
    def create(self, request):
        data = request.data or {}
        if not 'id' in data:
            raise BadRequestException("'id' is required")
        user = request.user
        username = "%s-%s" % (user.user_prefix, data.get('id'))
        u, created = User.objects.get_or_create(
                username=username,
                defaults={'is_active': False},
        )
        if not created:
            raise BadRequestException("already exists")
        return u

    PREFIX_RE = re.compile("\w+-(.*)")

    @classmethod
    def strip_prefix(cls, username):
        m = cls.PREFIX_RE.match(username)
        return m and m.group(1) or username 

    @classmethod
    def id(cls, obj):
        return cls.strip_prefix(obj.username)

    @uri
    def resource_uri(cls, obj):
        return users_handler, [cls.strip_prefix(obj.username)] 

class FilmsHandler(BaseHandler):
    model = Film
    fields = ('resource_uri', 'title', 'imdb_code', 'permalink', 'release_year')

    def read(self, request, imdb_code):
        return Film.objects.get(imdb_code=imdb_code)

    @uri
    def resource_uri(cls, obj):
        return films_handler, [obj.imdb_code]

class CreateRatingsMixin(object):
    def parse_rating(self, rating):
        if not rating:
            return None
        try:
            return int(rating)
        except ValueError, e:
            raise BadRequestException(unicode(e))

    def create_rating(self, request, data):
        if not 'rating' in data:
            raise BadRequestException("'rating' is required")
        if not self.user and not 'user_uri' in data:
            raise BadRequestException("'user_uri' is required")
        if not 'film_uri' in data:
            raise BadRequestException("'film_uri' is required")
        user = self.user or get_resource(request, data.get('user_uri'))
        film = get_resource(request, data.get('film_uri'))
        value = self.parse_rating(data.get('rating'))
        rating_helper.rate(user, value, film.id, skip_activity=True)
    
    def create_ratings(self, request):
        logger.info("data: %r", request.data)
        data = request.data
        if not isinstance(data, (dict, list)):
            raise BadRequestException("invalid input data")
        if isinstance(data, dict):
            data = [data]
        for item in data:
            self.create_rating(request, item)


class RatingsHandler(BaseHandler, CreateRatingsMixin):

    def create(self, request):
        self.user = None
        self.create_ratings(request)
        return self.SUCCESS_RESPONSE

    def read(self, request):
        raise http.Http404()

class UserRatingsHandler(BaseHandler, CreateRatingsMixin):

    def create(self, request, id):
        self.user = self.get_user(request, id)
        self.create_ratings(request)
        return self.SUCCESS_RESPONSE

    def read(self, request, id):
        user = self.get_user(request, id)
        ratings = rating_helper.get_user_ratings(user.id)
        return paginated_collection(request, [
                {
                    'film_uri': reverse(films_handler, args=[self.film_id_to_imdb_code(i)]),
                    'value': rating
                } for (i, rating) in ratings.items()
        ], default_limit=50)

class UserRecommendationsHandler(BaseHandler):
    
    def to_recommend_ids(self, request):
        tag = request.GET.get('tag')
        key = cache.Key('saas_to_recommend_ids', tag)
        film_ids = cache.get(key)
        if film_ids is None:
            if tag:
                film_ids = Film.objects.tagged(tag)
            else:
                film_ids = Film.objects.filter(popularity__gt=20)
            film_ids = list(film_ids.values_list('id', flat=True))
            cache.set(key, film_ids)
        return film_ids
    
    def read(self, request, id):
        from film20.new_recommendations.similarity_engine import reclist_from_similarities
        user = self.get_user(request, id)
        ratings = rating_helper.get_user_ratings(user.id)
        film_ids = self.to_recommend_ids(request)
        reclist = [
                {
                    'film_uri': reverse(films_handler, args=[self.film_id_to_imdb_code(id)])
                } for id in reclist_from_similarities(ratings, film_ids) if id not in ratings.keys()
        ]
        return paginated_collection(request, reclist, default_limit=50)

ratings_handler = Resource.register(RatingsHandler)
users_handler = Resource.register(UsersHandler)
user_ratings_handler = Resource.register(UserRatingsHandler)
user_recommendations_handler = Resource.register(UserRecommendationsHandler)
films_handler = Resource.register(FilmsHandler)

