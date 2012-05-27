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
import datetime

from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.db import IntegrityError, connection

from film20.config.urls import *
from film20.core.models import Object
from film20.core.models import Film
from film20.core.models import Person
from film20.core.models import Recommendation
from film20.core.models import Rating
from film20.core.models import FilmRanking
from film20.core.rating_form import RatingForm
from film20.recommendations.recom_helper import RecomHelper
from film20.utils import cache
from film20.utils.cache_helper import cache_query
from film20.core.deferred import defer
from film20.utils import redis_intf
from film20.recommendations import engine

from django.conf import settings
LANGUAGE_CODE = settings.LANGUAGE_CODE

import film20.settings as settings
# constants
RECOMMENDATION_ALGORITHM = getattr(settings, "RECOMMENDATION_ALGORITHM", "alg1")

import logging
logger = logging.getLogger(__name__)

def rate(user, value, film_id=None, actor_id=None, director_id=None, type=1, overwrite=True, check_if_exists=False, redis_only=False, skip_activity=False, **kw):
    if not user.id and hasattr(user, 'store_to_db'):
        # temporary anonymouse user, store to db on first rating
        user.store_to_db()

    assert user.id

    if not redis_only or not settings.USE_REDIS:
        if not settings.USE_REDIS:
            ret = Rating.rate(user, value, film_id, actor_id, director_id, type, overwrite=overwrite, _skip_activity=skip_activity, **kw)
        else:
            defer(Rating.rate, user, value, film_id, actor_id, director_id, type, overwrite=overwrite, _skip_activity=skip_activity, **kw)

    if settings.USE_REDIS:
        ret = redis_intf.rate(user.id, value, film_id, actor_id, director_id, type, overwrite=overwrite, check_if_exists=check_if_exists)

    profile = user.get_profile()
    no_rec = profile.recommendations_status == profile.NO_RECOMMENDATIONS

    if settings.RECOMMENDATIONS_ENGINE == 'film20.new_recommendations.recommendations_engine':
        engine.compute_user_features(user)
        if no_rec:
            profile.recommendations_status = profile.FAST_RECOMMENDATIONS
            profile.save()
    else:
        if no_rec and len(get_user_ratings(user.id)) >= settings.RECOMMENDATIONS_MIN_VOTES_USER:
            engine.compute_user_features(user, True, initial=True)
            profile.recommendations_status = profile.FAST_RECOMMENDATIONS
            profile.save()
    return ret

def get_rating(user, film_id=None, actor_id=None, director_id=None, type=1):
    if settings.USE_REDIS:
        return redis_intf.get_rating(user.id, film_id=film_id, actor_id=actor_id, director_id=director_id, type=type)
    else:
        return Rating.get_rating(user, film_id=film_id, actor_id=actor_id, director_id=director_id, type=type)

def get_user_ratings(user_id):
    return Rating.get_user_ratings(user_id)

def get_ratings(film_id=None, actor_id=None, director_id=None, type=1):
    if settings.USE_REDIS:
        return redis_intf.get_ratings(film_id=film_id, actor_id=actor_id, director_id=director_id, type=type)
    return Rating.get_ratings(film_id=film_id, actor_id=actor_id, director_id=director_id, type=type)

def get_film_ratings(film_id):
    return get_ratings(film_id)

def get_seen_films(user):
    if settings.USE_REDIS:
        seen_ids = redis_intf.get_seen_films(user)
    else:
        seen_ids = Film._recently_seen_film_ids(user)
        seen_ids.difference_update(Film._long_ago_seen_film_ids(user))
    return seen_ids

def mark_films_as_seen(user, film_ids):
    if settings.USE_REDIS:
        redis_intf.mark_films_as_seen(user, film_ids)
    else:
        Film.mark_films_as_seen(user, film_ids)

class BaseRater(object):
    def __init__(self, request):
        self.user = request.unique_user

    # public interface
    def get_films_to_rate(self, number_of_films=1, tag=None):
        raise NotImplementedError()

    def rate_film(self, film_id, rating, type=1):
        raise NotImplementedError()

    def mark_films_as_seen(self, film_ids):
        mark_films_as_seen(self.user, film_ids)

    def get_seen_films(self):
        return get_seen_films(self.user)

class BaseBasketsRater(BaseRater):

    BASKETS_TAGS_LIST = settings.BASKETS_TAGS_LIST
    NUMBER_OF_FILMS_RELATED = settings.NUMBER_OF_FILMS_RELATED
    SPECIAL_BASKET_BONUS = settings.SPECIAL_BASKET_BONUS
    SPECIAL_RATE_BASKET_SIZE = settings.SPECIAL_RATE_BASKET_SIZE
    TAG_BASKET_SIZE = settings.TAG_BASKET_SIZE
    MIN_TAG_BASKET_SIZE = settings.MIN_TAG_BASKET_SIZE
    RATE_BASKET_SIZE = settings.RATE_BASKET_SIZE
    MIN_RATE_BASKET_SIZE = settings.MIN_RATE_BASKET_SIZE
    MIN_RATE_FOR_SPECIAL_BASKET = settings.MIN_RATE_FOR_SPECIAL_BASKET

    def cache_key(self, prefix, *args, **kw):
        return cache.Key(prefix, self.__class__.__name__, 'v3', *args, **kw)

    def _clear_baskets(self, user):
        for tag in self.BASKETS_TAGS_LIST:
            cache.delete(self.cache_key(cache.CACHE_TAG_BASKET, user, tag))
        cache.delete(self.cache_key(cache.CACHE_USER_BASKET, user))
        cache.delete(self.cache_key(cache.CACHE_SPECIAL_USER_BASKET, user))

    def refill_user_baskets(self, user):
        for tag in self.BASKETS_TAGS_LIST:
            self.refill_tag_basket(user, tag)
        self.refill_user_basket(user)

    def delete_from_tag_basket(self, user, id, tag):
        basket_key = self.cache_key(cache.CACHE_TAG_BASKET, user, tag)
        tag_basket = cache.get(basket_key) or dict()
        if id in tag_basket:
            tag_basket.pop(id)
        cache.set(basket_key, tag_basket, cache.A_MONTH)

    def delete_film_from_baskets_by_id(self, user, film_id):
        # delete from tag baskets
        for tag in self.BASKETS_TAGS_LIST:
            self.delete_from_tag_basket(user, film_id, tag)

        defer(self.refill_tag_baskets, user, self.BASKETS_TAGS_LIST)

        # delete from regular basket
        rating_basket_key = self.cache_key(cache.CACHE_USER_BASKET, user)
        rating_basket = cache.get(rating_basket_key) or set()
        rating_basket.discard(film_id)
        cache.set(rating_basket_key, rating_basket, cache.A_MONTH)

        # delete from special basket
        special_rating_basket_key = self.cache_key(cache.CACHE_SPECIAL_USER_BASKET,
                user)
        special_rating_basket = cache.get(special_rating_basket_key) or set()
        special_rating_basket.discard(film_id)
        cache.set(special_rating_basket_key, special_rating_basket, cache.A_MONTH)

    def get_related_film_ids(self, film_id):
        key = self.cache_key("rater_related_films", film_id)
        related = cache.get(key)
        if related is None:
            film = Film.objects.get(id=film_id)
            related = list(film.get_related_films().values_list('id', flat=True)[:self.NUMBER_OF_FILMS_RELATED])
            cache.set(key, related)
        return related

    def add_films_to_special_basket_by_film_id(self, user, film_id):

        rating_basket_key = self.cache_key(cache.CACHE_USER_BASKET, user)
        special_rating_basket_key = self.cache_key(cache.CACHE_SPECIAL_USER_BASKET,
                user)
        rating_basket = cache.get(rating_basket_key) or set()
        special_rating_basket = cache.get(special_rating_basket_key) or set()
        new_basket = []

        related = self.get_related_film_ids(film_id)

        excluded = self.get_excluded_films()

        if related:
            new_basket = set(related) - excluded
            new_basket = set(list(new_basket)[:self.SPECIAL_BASKET_BONUS])

        if new_basket:
            # how many we leave from the previous basket
            left_number = self.SPECIAL_RATE_BASKET_SIZE - len(new_basket)
            basket_list = list(special_rating_basket)

            # we throw old films to normal basket
            rating_basket.update(set(basket_list[left_number:]))
            # we leave some old ones in special basket
            new_basket.update(set(basket_list[:left_number]))

            cache.set(rating_basket_key, rating_basket, cache.A_MONTH)
            cache.set(special_rating_basket_key, new_basket, cache.A_MONTH)

    def refill_tag_baskets(self, user, tags):
        for tag in tags:
            self.refill_tag_basket(user, tag)

    def get_films(self):
        return Film.objects.all()

    def get_film_ids_by_tag(self, tag='', lang='pl'):
        """ Returns dict(id, popularity) for films with given tag"""

        key = self.cache_key("films_by_tag", tag, lang)
        films = cache.get(key)
        if films is None:
            films = self.get_films()
            if tag:
                films = films.tagged(tag)
            if lang == 'en':
                films = films.exclude(production_country_list='Poland')
            films = dict(films.values_list('parent_id', 'popularity'))
            cache.set(key, films)

        return films


    def refill_tag_basket(self, user, tag):

        # lang = user.id and user.get_profile().LANG or settings.LANGUAGE_CODE
        lang = settings.LANGUAGE_CODE

        basket_key = self.cache_key(cache.CACHE_TAG_BASKET, user, tag)
        tag_basket = cache.get(basket_key) or dict()

        if len(tag_basket) < self.MIN_TAG_BASKET_SIZE:
            # get films with this tag
            films_dict = self.get_film_ids_by_tag(tag, lang)
            excluded = self.get_excluded_films()
            # remove films seen by user
            films_dict = dict([(k,v) for k,v in films_dict.items() if k not in excluded])
            # how many we want to refill
            to_refill = self.TAG_BASKET_SIZE - len(tag_basket)
            # reverse sort by popularity
            sorted_films = sorted(films_dict, key=films_dict.get, reverse=True)[:to_refill]
            refill_dict = dict([(fid, films_dict[fid]) for fid in sorted_films])

            tag_basket.update(refill_dict)
            cache.set(basket_key, tag_basket, cache.A_MONTH)

    def get_from_tag_basket(self, user, tag, number_of_films=1):

        basket_key = self.cache_key(cache.CACHE_TAG_BASKET, user, tag)

        no_films_key = self.cache_key("no_films_left_for_tag", user, tag)
        # indicates whether there are any films left to show to user
        no_films = cache.get(no_films_key)

        if not no_films:
            tag_basket = cache.get(basket_key) or dict()
            if len(tag_basket) < number_of_films:
                self.refill_tag_basket(user, tag)
                tag_basket = cache.get(basket_key) or dict()

            result = sorted(tag_basket, key=tag_basket.get,
                    reverse=True)[:number_of_films]

            if not result:
                cache.set(no_films_key, True, cache.A_MONTH)
            else:
                for film_id in result:
                    tag_basket.pop(film_id)
                cache.set(basket_key, tag_basket, cache.A_MONTH)
                defer(self.refill_tag_basket, user, tag)

            return result
        else:
            return []

    def refill_user_basket(self, user):
        rating_basket_key = self.cache_key(cache.CACHE_USER_BASKET, user)
        rating_basket = cache.get(rating_basket_key) or set()
        seen_films = self.get_excluded_films()
        if len(rating_basket) < self.MIN_RATE_BASKET_SIZE:
            while len(rating_basket) < self.RATE_BASKET_SIZE:
                size = len(rating_basket) # we will check if it changes
                for tag in self.BASKETS_TAGS_LIST:
                    films = self.get_from_tag_basket(user, tag, number_of_films=1)
                    if films and films[0] not in seen_films:
                        rating_basket.update(films) 
                # if the size hasn't changed
                if len(rating_basket) <= size:
                    break

            cache.set(rating_basket_key, rating_basket, cache.A_MONTH)

    def get_films_to_rate(self, number_of_films=1, tag=None):

        if not tag:
            rating_basket_key = self.cache_key(cache.CACHE_USER_BASKET, self.user)
            special_rating_basket_key = self.cache_key(cache.CACHE_SPECIAL_USER_BASKET,
                    self.user)
            rating_basket = cache.get(rating_basket_key) or set()
            special_rating_basket = cache.get(special_rating_basket_key) or set()
            rating_basket.difference_update(special_rating_basket)
            if len(rating_basket) + len(special_rating_basket) < number_of_films:
                self.refill_user_basket(self.user)
                rating_basket = cache.get(rating_basket_key) or set()
                rating_basket.difference_update(special_rating_basket)

            result = list(special_rating_basket) + list(rating_basket)
            result = result[:number_of_films]
            result_set = set(result)
            rating_basket.difference_update(result_set)
            special_rating_basket.difference_update(result_set)

            cache.set(rating_basket_key, rating_basket, cache.A_MONTH)
            cache.set(special_rating_basket_key,
                    special_rating_basket, cache.A_MONTH)
        else:
            result = self.get_from_tag_basket(self.user, tag, number_of_films=number_of_films)

        films = list(Film.objects.filter(id__in=result).select_related())
        return films

    def rate_film(self, film_id, rating, type=1):
        rate(self.user, rating, film_id=film_id, type=type)
        if rating and rating >= self.MIN_RATE_FOR_SPECIAL_BASKET:
            self.add_films_to_special_basket_by_film_id(self.user, film_id) 
        self.delete_film_from_baskets_by_id(self.user, film_id)

    def get_excluded_films(self):
        ids = set()
        ids.update(self.get_seen_films())
        if self.user.id:
            ids.update(Rating.get_user_ratings(self.user).keys())
            ids.update(Film._marked_film_ids(self.user))
        return ids

class BasketsRater(BaseBasketsRater):
    pass

def get_rater(request):
    rater = request.REQUEST.get('rater')
    if rater == 'vue':
        from film20.vue.rater import VueRater
        return VueRater(request)
    return BasketsRater(request)

def set_rater(request, rater_class):
    request.session['rater_class'] = rater_class

def handle_rating(rating_form, user):
    """
    Handles the rating form. Depending on action, calls the insert or update method
    """
    if rating_form.is_valid():                   
        edit_id = rating_form.cleaned_data['edit_id']
        cancel_rating = rating_form.cleaned_data['cancel_rating']
        
        if cancel_rating == 1:
            logger.debug("Cancelling rating...")
            return cancel_rating(rating_form, user)
        else:
            logger.debug("Adding/editing rating...")
            return add_edit_rating(rating_form, user)
    else:
        logger.debug("Rating form invalid!, %s",repr(rating_form.errors))
        return rating_form 

def add_edit_rating(rating_form, user):
    """
        Creates a new rating for a given object and user based on the rating_form passed.

        Warning: one_rating_for_user_parent_type constraint may be violated if case the
            same method gets called twice with identical parameters and the function
            tries to insert a new rating twice. This is handled quietly, check
            http://jira.filmaster.org/browse/FLM-407 for details.
    """
    rating = rating_form.cleaned_data['rating']    
    object_id = rating_form.cleaned_data['object_id']
    form_type = rating_form.cleaned_data['form_type']
    object = Object.objects.get(id=object_id)            

    rated_object = get_rated_object(form_type, object_id)

    extra = {}
    if rating_form.cleaned_data.get('actor_id',False):
        extra['actor'] = rating_form.cleaned_data['actor_id']
    
    now = datetime.datetime.now()
        
    defaults = {
        'first_rated': now,
        'last_rated': now,
        'rating':rating,
    }

    fkeys = foreign_keys(form_type, rated_object)
    defaults.update(fkeys)
                
    r, created = Rating.objects.get_or_create(
        user=user,
        parent=object,
        type=form_type,
        defaults=defaults,
        **extra
    )
    if not created:
        r.rating = rating
        r.last_rated = now
        r.__dict__.update(fkeys)
        r.save()

    # update the popularity of the rated object
    
    field = {
        Rating.TYPE_ACTOR: 'actor_popularity',
        Rating.TYPE_DIRECTOR: 'director_popularity',
        Rating.TYPE_FILM: 'popularity',
    }.get(form_type, None)

    if field is not None:
        setattr(rated_object, field, (getattr(rated_object, field, 0) or 0) + 1)
        rated_object.save()
        logger.info('%r updated', field)

    return rating_form

def edit_rating(rating_form, user):
    """
    Updates rating for a given object and user basing on the rating_form passed
    """
    rating = rating_form.cleaned_data['rating']    
    object_id = rating_form.cleaned_data['object_id']
    edit_id = rating_form.cleaned_data['edit_id']
    form_type = rating_form.cleaned_data['form_type']
    user_id = user.id

    # Set data depending on the rated object        
    # Check if rated object exists for this parent object
    rated_object = get_rated_object(form_type, object_id)
    
    try:                                
        # save the rating
        r = Rating.objects.get(
            user = user.id, 
            parent = object_id,
            type = form_type,
        )                
        r.rating = rating
        populate_foreign_key(form_type, r, rated_object)
        r.last_rated =  datetime.datetime.now()
        r.save()                       
    except (Rating.DoesNotExist, Rating.MultipleObjectsReturned), e:
        logger.error(unicode(e)) 

    return rating_form

def cancel_rating(rating_form, user):
    """
    Cancels rating for a given object and user basing on the rating_form passed
    """
    rating = rating_form.cleaned_data['rating']    
    object_id = rating_form.cleaned_data['object_id']
    edit_id = rating_form.cleaned_data['edit_id']
    form_type = rating_form.cleaned_data['form_type']
    user_id = user.id

    # Set data depending on the rated object        
    # Check if rated object exists for this parent object
    rated_object = get_rated_object(form_type, object_id)
    logger.debug("rated_object = " + unicode(rated_object))
    
    try:                                
        # save the rating
        r = Rating.objects.get(
            user = user.id, 
            parent = object_id,
            type = form_type,
        )                
        r.rating = None
        populate_foreign_key(form_type, r, rated_object)
        r.last_rated =  datetime.datetime.now()
        logger.debug("r = " + unicode(r))            
        r.save()                       
        
    except (Rating.DoesNotExist, Rating.MultipleObjectsReturned), e:
        logger.error(unicode(e)) 

    return rating_form

def get_ranking(object_id, type=Rating.TYPE_FILM):
    """
        Gets average rating for film in a given category
    """
    query = (                
        Q(film__id = object_id) &
        Q(type = type)
    )
    ranking = FilmRanking.objects.get(query)
    logger.debug("Average ranking for film fetched: " + unicode(ranking.average_score))

    return ranking

def revert_rating(rating):
    if rating != None:
        return 11 - rating
    else:
        return None

def get_rated_object(form_type, object_id):
    # Set data depending on the rated object
    if form_type == Rating.TYPE_ACTOR:
        Type = Person
        query = (
            Q(parent=object_id) &
            Q(is_actor=True)
        )
    elif form_type == Rating.TYPE_DIRECTOR:
        Type = Person
        query = (
            Q(parent=object_id) &
            Q(is_director=True)
        )
    else:
        Type = Film
        query = (
            Q(parent=object_id)
        )
        
    rated_object = Type.objects.get(query)
    return rated_object

def foreign_keys(form_type, rated_object):
    d = {}
    if form_type == Rating.TYPE_ACTOR:
        logger.debug("Setting director to rated_object")
        d['actor'] = rated_object
    elif form_type == Rating.TYPE_DIRECTOR:
        logger.debug("Setting director to rated_object")
        d['director'] = rated_object
    else:                
        logger.debug("Setting film to rated_object")
        d['film'] = rated_object
    return d

def populate_foreign_key(form_type, r, rated_object):
    r.__dict__.update(foreign_keys(form_type, rated_object))
    return r

# FILM DEFAULT FORM    
def get_default_rating_form(object_id, form_type,**extra):
    """
    Returns a default rating form (main one)
    """
    initial= {
      'object_id' : object_id,
      'form_type' : form_type,
      'cancel_rating' : '0',
    }
    initial.update(extra)
    return RatingForm(initial=initial)

def get_rating_form(user_id, object_id, form_type, **extra):
    """
    Returns rating for user, object id and type 
    """
    try:
        # User already rated this movie - populated form
        kwargs = {
         'user':user_id,
         'parent':object_id,
         'type':form_type,
         'normalized__isnull':False
        }
        kwargs.update(extra)
        return Rating.objects.get(**kwargs)
    except Rating.DoesNotExist:
        # User never rated this movie
        return None
    

def generate_rating_form(user_id, object_id, form_type, rating=None, **extra):
    """
    Generates a rating form (main one) for given form for a logged in user
    Returns default form if the user never voted, or an edit form if the user already voted 
    """
#        short_review_text = ""
    
    # User already rated this movie - populated form
    if rating == None:
        return get_default_rating_form(object_id, form_type,**extra)
    initial= {
            'rating' : rating.rating,      
            'edit_id' : rating.id,
            'object_id' : object_id,
            'form_type' : form_type,
            'cancel_rating' : '0',
    }
    initial.update(extra)
    rating_form = RatingForm(initial=initial)                 
     
    return rating_form

# FILM EXTRA FORMS    
def get_default_film_extra_rating_single_form(the_film, rating_type):
    """
    Returns a default film rating form (extra one, for particular type)
    """
    return RatingForm(
        initial= {
            'object_id' : the_film.parent.id,
            'form_type' : rating_type,
        }
    )
    
def get_default_film_rating_extra_forms(the_film):
    """
    Generates the whole list of default extra rating forms for given film
    These do not include actor rating forms, only the extra film parameters rating
    """

    default_film_rating_extra_forms = {}        
    for rating_type in Rating.ADVANCED_RATING_TYPES:
        default_film_rating_extra_forms[rating_type] = get_default_film_extra_rating_single_form(the_film, rating_type)
    return default_film_rating_extra_forms
        
def generate_film_extra_rating_single_form(request, the_film, rating_type):
    """
    Generate a single extra rating parameter rating form for given film and parameter (rating) type for a logged in user
    Returns default form if the user never voted, or an edit form if the user already voted
    """
    try:
        # User already rated this movie - populated form
        rating = Rating.objects.get(
                user = request.user.id, 
                parent = the_film.parent.id,
                type = rating_type,
                actor__isnull = True,
                director__isnull = True,
            )
        film_rating_form = RatingForm(
            initial= {
                'rating' : rating.rating,      
                'edit_id' : rating.id,
                'object_id' : the_film.parent.id,
                'form_type' : rating_type,
                'cancel_rating' : '0',
            }
        )     
        logger.debug("Found value for extra form!")            
    except Rating.DoesNotExist:
        logger.debug("Found NO value for extra form!")
        # User never rated this movie - clear form
        film_rating_form = get_default_film_extra_rating_single_form(the_film, rating_type)
    return film_rating_form

def generate_film_rating_extra_forms(request, the_film):
    """
    Generates the whole list of extra ratings forms for given film
    These do not include actor rating forms, only the extra film parameters rating
    """        
    film_rating_extra_forms = {}        
    for rating_type in Rating.ADVANCED_RATING_TYPES:
        film_rating_extra_forms[rating_type] = generate_film_extra_rating_single_form(request, the_film, rating_type)
    return film_rating_extra_forms

def get_rating_type_label(type):
    # Yes, this is pretty ugly, but it should just work and it's faster than using a hash table 
    # and less coding at the same time (no need to define the same thing twice for 'choices' field in
    # Rating model and for display (michuk) 
    # Generally, this returns the tuple with given ID and takes the second element 
    # from it that should be the display string
    return Rating.ALL_RATING_TYPES[int(type)-1][Rating.INDEX_LABEL]
    
# TODO: properly
def map_extra_forms_to_list(film_rating_extra_forms):
    # if no film form, return null list
    if film_rating_extra_forms==None:
        logger.error("No film_rating_extra_forms found, returning an empty list!")
        return []

    film_rating_extra_forms_as_list = []        
    for rating_type in Rating.ADVANCED_RATING_TYPES:
        film_rating_extra_forms_as_list += {'form':film_rating_extra_forms[rating_type], 'type':rating_type,},
    return film_rating_extra_forms_as_list

def get_movies_to_be_rated_from_session(request):

    films_to_be_rated_user = request.session.get('films_to_be_rated_user', False)

    if films_to_be_rated_user:
        # hack for not-logged-in users
        if request.user.is_authenticated() == False:
            user_id = 1
        else:
            user_id = request.user.id
        if films_to_be_rated_user == user_id:
            if request.session.get('films_to_be_rated', False):
                logger.debug("films_to_be_rated found in session for current user.")
                return request.session['films_to_be_rated']
            else:
                logger.debug("No films_to_be_rated in session for current user.")
                return None
        else:
            logger.debug("Films in session are for a different user!")
            return None
    else:
        logger.debug("No films_to_be_rated_user in session for current user.")
        return None
    
def store_movies_to_be_rated_in_session(request, films_to_be_rated):       
    request.session['films_to_be_rated'] = films_to_be_rated

    # hack for not-logged-in users
    if request.user.is_authenticated() == False:
        user_id = 1
    else:
        user_id = request.user.id

    request.session['films_to_be_rated_user'] = user_id
    
def get_rated_movies_from_session(request):
    if request.session.get('rated_movies', False):            
        return request.session['rated_movies']
    else:           
        return None          
            
def store_rated_movie_in_session(request, object_id):
    rated_movies = [object_id,]
            
    if request.session.get('rated_movies', False):
        logger.debug("Session: rated_movies not is empty:")
        logger.debug(request.session['rated_movies'])
        
        # add the film to the rated list
        request.session['rated_movies'] = request.session['rated_movies'] + rated_movies
    else:                       
        logger.debug("Session: rated_movies is empty")
        request.session['rated_movies'] = rated_movies

def get_ratings_for_user_and_film(user, film):
    qset = (
        Q(user = user.id) &
        Q(parent = film.parent.id) &
        Q(rating__isnull=False)
    )
    ratings = Rating.objects.select_related().filter(qset).order_by("type")
    logger.debug("Ratings for author" + unicode(ratings))
    
    map = {}
    for rating in ratings:
        map[rating.type] = rating
            
    return map   
