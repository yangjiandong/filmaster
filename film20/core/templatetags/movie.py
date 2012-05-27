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
# Python
import random
import logging
import pytz, datetime

# Django
from django.utils.translation import gettext_lazy as _, gettext
from django.contrib.auth.models import User
from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
# Project
from film20.config.urls import *
from film20.showtimes.models import Channel, ScreeningCheckIn, TYPE_TV_CHANNEL, TYPE_CINEMA
from film20.showtimes.showtimes_helper import collect_unique_films, \
        get_theaters, get_tv_channels, get_today
from film20.core.models import Rating, Film
from film20.core.rating_form import FilmRatingForm, SimpleFilmRatingForm
from film20.core.film_helper import FilmHelper
from film20.filmbasket.models import BasketItem
from film20.recommendations.recom_helper import RecomHelper
from film20.utils import cache_helper as cache
from film20.utils.cache_helper import CACHE_ACTIVITIES, CACHE_HOUR, A_DAY
from film20 import recommendations

logger = logging.getLogger(__name__)

from film20.utils.template import Library
register = Library()

from film20.utils.cache import cache_query

@register.inclusion_tag('movies/movie/actors.html', takes_context=True)
def film_actors(context, film, n=5):
    actors = cache_query(film.get_actors(), 'film_actors', film)
    return {
        'film':film,
        'perms':context.get('perms'),
        'actors':actors,
    }

@register.inclusion_tag('movies/movie/directors.html', takes_context=True)
def film_directors(context, film):

    directors = film.get_directors()

    return {
        'film':film,
        'perms':context.get('perms'),
        'directors':directors,
    }

from django.utils.html import strip_tags
from django.utils.text import truncate_words

@register.inclusion_tag('movies/movie/description.html', takes_context=True)
def film_description(context, film, words=None, edit=False):
    short = False
    if film.description:
        descr = unicode(strip_tags(film.description))
    else:
        if film.is_tv_series:
            descr = gettext("Unfortunately, this tv series does not have a description, yet.")
        else:
            descr = gettext("Unfortunately, this film does not have a description, yet.")
    if (not film.description) and film.imdb_code:
        imdb_address = "http://imdb.com/title/tt" + str(film.imdb_code) + "/"
        descr += _("\nYou can try ") + \
                "<a href=\"" + imdb_address + "\">IMDB</a>."
    if words:
        description = unicode(truncate_words(descr, words))
        short = True
    else:
        description = descr
    return {
        'film':film,
        'edit':edit,
        'can_edit': context['request'].user.is_authenticated(),
        'description':description,
        'short': short
    }

from film20.core.film_helper import FilmHelper
film_helper = FilmHelper()
        
from film20.core.models import FilmLocalized
@register.inclusion_tag('movies/movie/related.html', takes_context=True)
def film_related(context, film):
    NUMBER_RELATED = getattr(settings, 'NUMBER_OF_FILMS_RELATED', 6)
    related = cache_query(film.get_related_films()[:NUMBER_RELATED],
            "film_related_films", film)
    return {
        'film':film,
        'perms':context.get('perms'),
        'related':related,
    }

@register.widget('movies/movie/ratings.html', lambda film:dict(film_id=film.id))
def film_similar_ratings(request, film=None):
    user = request.user
    film = film or get_object_or_404(Film, id=request.GET.get('film_id'))
    ratings = ()
    if user.is_authenticated():
        key = cache.Key("film_similar_ratings", film, user)
        ratings = cache.get(key)
        if ratings is None:
            N_SIMILAR = 100
            N = 5
            query = User.objs.similar(user)[:N_SIMILAR]
            similar_users = cache_query(query, "similar_users", user)
            if similar_users:
                d = dict((u.id, u) for u in similar_users)
                ratings = Rating.objects.select_related()
                ratings = list(ratings.film(film).filter(user__in=d.keys()))
                ratings = sorted(ratings, key=lambda r:d[r.user_id].score)[:N]
                logger.debug("%d of %d similar friends rated this film", len(ratings), N_SIMILAR)
                if len(ratings)<N:
                    logger.debug("not enough results, executing full query")
                    ratings = Rating.objects.select_related()
                    ratings = ratings.film(film).similar_ratings(user)[0:N]
                    logger.debug("similar ratings fetched")
            cache.set(key, ratings)
    link = film.get_absolute_url()
    link = str(link) + '?u=similar'
    return {
        'film':film,
        'title':_("Similar users ratings"),
        'link':link,
        'ratings':ratings,
        'friends': False
    }

@register.widget('movies/movie/ratings.html', lambda film:dict(film_id=film.id))
def film_friends_ratings(request, film=None):
    user = request.user
    film = film or get_object_or_404(Film, id=request.GET.get('film_id'))
    if user.is_authenticated():
        ratings = cache_query(film.get_friends_ratings(user), "film_friends_ratings", film, user)
    else:
        ratings = ()
    link = film.get_absolute_url()
    link = str(link) + '?u=friends'
    return {
        'film':film,
        'title':_("Friends ratings"),
        'link':link,
        'ratings':ratings,
        'friends': True,
        'user_rated': film.is_rated_by_user( user )
    }

@register.simple_tag
def rating_description( value ):
    texts = {
        1 : _( 'disaster' ),
        2 : _( 'very bad' ),
        3 : _( 'poor' ),
        4 : _( 'below average' ),
        5 : _( 'average' ),
        6 : _( 'above average' ),
        7 : _( 'good' ),
        8 : _( 'very good' ),
        9 : _( 'exceptional' ),
        10: _( 'masterpiece' )
    }
    if texts.has_key( value ):
        return texts[value]
    return ""

@register.filter
def default_tr(value, default):
    return value or _(default)

from film20.core import rating_helper

@register.inclusion_tag('movies/movie/score.html', takes_context=True)
def film_score(context, film, user, type=1):
    from django.template import Context
    ctx = Context(context)
    ctx['film'] = film
    ctx['user'] = user
    ctx['type'] = type
    return ctx

@register.inclusion_tag('movies/movie/average_score.html', takes_context=True)
def film_average_score(context, film, user, type=1):
    return {
        'film':film,
        'perms':context.get('perms'),
        'average':film.average_score(),
        'votes': film.number_of_votes(),
        'type':type,
    }

@register.inclusion_tag('movies/movie/user_rating.html', takes_context=True)
def film_user_rating(context, film, user, type='SIMPLE'):
    R_TYPES = dict(Rating.ALL_RATING_TYPES)

    key = cache.Key(film, user, type)
    ratings = cache.get(key)

    simple = True
    if type == 'DETAILED':
        simple = False

    if not ratings:
            if type == 'DETAILED':
                ratings = Rating.objects.filter(film=film.id,
                        user=user, type__in=R_TYPES.keys(), rating__isnull=False).order_by('type').values('rating', 'type')
            else:
                ratings = Rating.objects.filter(film=film.id,
                        user=user, type=Rating.TYPE_FILM,
                        rating__isnull=False).values('rating', 'type')

            for rate in ratings:
                rate['desc'] = R_TYPES[rate['type']]

            cache.set(key, ratings)

    return {
        'film':film,
        'ratings':ratings,
        'simple': simple,
    }

@register.inclusion_tag('movies/movie/rating_for_user.html', takes_context=True)
def film_rating_for_user(context, film, user, type=''):
    request = context['request']
    rating = None
    guess = None
    try:
        rating = Rating.objects.get(film=film.id,
                user=user, rating__isnull=False, type=Rating.TYPE_FILM)
    except Rating.DoesNotExist, e:
        rating = None

    if not rating:
        if user.is_authenticated():
            guess = recommendations.engine.compute_guess_score(user, film.pk)
        else:
            guess = None

    return {
        'film':film,
        'rating':rating,
        'guess': guess,
        'request': request
    }

@register.inclusion_tag('movies/movie/guess_score.html', takes_context=True)
def film_guess_score(context, film, user, type=1):
    if user.is_authenticated() and not film.is_rated_by_user( user ):
        guess = recommendations.engine.compute_guess_score(user, film.pk)
    else:
        guess = None
    return {
        'film':film,
        'perms':context.get('perms'),
        'guess':guess,
        'type':type,
    }

@register.setcontexttag
def set_guess_score(film, user):
    if user.is_authenticated() and not film.is_rated_by_user( user ):
        if hasattr(film, 'guess_rating'):
            guess = film.guess_rating
        else:
            guess = recommendations.engine.compute_guess_score(user, film.pk)
    else:
        guess = None
    return {
        'guess_score': guess,
    }


from film20.useractivity.models import UserActivity

@register.inclusion_tag('movies/movie/featured_reviews.html', takes_context=True)
def film_featured_posts(context, film):
    activities = UserActivity.objects.public().filter(film=film.id, activity_type=UserActivity.TYPE_POST, featured=True)[0:2]
    activities = cache_query(activities, "film_featured_posts", film)
    return {
        'film':film,
        'activities':activities,
    }

from film20.showtimes.showtimes_helper import ScreeningSet

@register.widget('movies/movie/cinema_screenings.html', lambda film:dict(film_id=film.id))
def film_cinema_screenings(request, film=None):
    user = request.user
    film = film or get_object_or_404(Film, id=request.GET.get('film_id'))
    today = get_today(request.timezone)
    days = []
    towns = ()

    MAX_NUMBER_OF_SCREENINGS = getattr(settings, 'MAX_NUMBER_OF_SCREENINGS', 8)

    channels = get_theaters(request) or ()

    for n, name in enumerate((_("Today"), _("Tomorrow"), _("Day After Tomorrow"))):
        date = today + datetime.timedelta(days=n)
        screening_set = ScreeningSet(date, channels)
        playing = screening_set.get_channels(film.id)
        if playing:
            days.append({'name':name, 'channels':playing})

    return {
        'film':film,
        'days':days,
        'towns_playing': towns,
    }

@register.widget('movies/movie/tv_screenings.html', lambda film:dict(film_id=film.id))
def film_tv_screenings(request, film=None):
    user = request.user
    film = film or get_object_or_404(Film, id=request.GET.get('film_id'))
    today = get_today(request.timezone)
    days = []
    channels = get_tv_channels(request)
    for n, name in enumerate((_("Today"), _("Tomorrow"), _("Day After Tomorrow"))):
        date = today + datetime.timedelta(days=n)
        screening_set = ScreeningSet(date, channels)
        playing = screening_set.get_channels(film.id)
        if playing:
            days.append({'name':name, 'channels':playing})
    return {
        'film':film,
        'days':days,
    }

@register.widget('movies/movie/others_ratings.html', lambda film:dict(film_id=film.id))
def film_others_ratings(request, film=None):
    film = film or Film.objects.get(id=request.GET.get('film_id'))
    return {
        'film':film,
    }

@register.inclusion_tag('movies/rating/ratings_form.html', takes_context=True)
def film_ratings_form(context, film, edit=False):
    request = context.get('request')
    form = FilmRatingForm(None, request, film, edit=edit)
    return {
        'film':film,
        'form':form,
        'request':request,
    }

@register.inclusion_tag('movies/rating/single_film_ratings_form.html', takes_context=True)
def single_film_ratings_form(context, film):
    """
        Displays film ratings form but with rate more link instead of rate next
    """
    return film_ratings_form(context, film, edit=True)

@register.inclusion_tag('movies/rating/ratings_form_simple.html', takes_context=True)
def film_ratings_form_simple(context, film):
    request = context.get('request')
    form = SimpleFilmRatingForm(None, request, film)
    return {
        'film':film,
        'form':form,
        'request':request,
        'collection_view':context.get('collection_view', False),
    }

@register.inclusion_tag('movies/rating/add_edit_film_rate_form.html',
        takes_context=True)
def add_edit_film_rate_form(context, film):
    request = context.get('request')
    form = SimpleFilmRatingForm(None, request, film)
    return{
        'film': film,
        'form': form,
        'request': request,
    }

@register.inclusion_tag('movies/rating/ratings_form_special.html', takes_context=True)
def film_ratings_form_with_target(context, film, target=''):
    request = context.get('request')
    form = SimpleFilmRatingForm(None, request, film)
    return {
        'film':film,
        'form':form,
        'request':request,
        'target': target,
    }

@register.simple_tag(takes_context=True)
def film_ratings_form_special(context, film, template_dir=None):
    request = context.get('request')
    form = SimpleFilmRatingForm(None, request, film)
    template = 'movies/rating/ratings_form_special.html'
    if template_dir:
        template = "%s/%s" % (template_dir, template)
    context = {
        'film':film,
        'form':form,
        'request':request,
    }
    
    return render_to_string(template, context)

def top_recommendations_tv(context, films_number=4):
    """
        Displays user's top recommended movies in tv
        (most popular for not logged in).
    """

    request = context['request']
    user = context.get( 'recommendations_user', request.user )

    key = cache.Key("tv_user_recommended", user)
    films = cache.get(key)
    if films is None:
        channels = get_tv_channels(request)
        now = get_today(request.timezone)
        films = collect_unique_films(now, channels, films_number, days=3, user=user)
        cache.set(key, films)
    return films

def top_recommendations_cinema(context, films_number=4):
    """
        Displays user's top recommended movies in cinemas
        (most popular for not logged in).
    """

    request = context['request']
    user = context.get( 'recommendations_user', context['request'].user )

    key = cache.Key("cinema_user_recommended", user)
    films = cache.get(key)
    if films is None:
        channels = get_theaters(request)
        now = get_today(request.timezone)
        films = collect_unique_films(now, channels, films_number, days=3, user=user)
        cache.set(key, films)
    return films

def top_recommendations_all(context, films_number=4):
    """
        Displays user's top recommended movies
        (most popular for not logged in).
    """
    POPULAR_FILMS_NUMBER_ALL = getattr(settings,
            'POPULAR_FILMS_MAIN_PAGE_NUMBER_ALL')

    user = context.get( 'recommendations_user', context['request'].user )
    key = cache.Key("popular_films_main_page", user)

    films = cache.get(key)
    if (not films) or len(films) < films_number:

        key_all = cache.Key("popular_films_main_page_all", user)
        all_films = cache.get(key_all)
        if not all_films:
            has_recommendations = user.is_authenticated() and \
                    user.get_profile().recommendations_status
            if has_recommendations:
                recom_helper = RecomHelper()
                all_films = list(recom_helper.get_best_psi_films_queryset(user)[:POPULAR_FILMS_NUMBER_ALL])
            else:
                fhelper = FilmHelper()
                all_films = list(fhelper.get_popular_films(
                        number_of_films=POPULAR_FILMS_NUMBER_ALL,
                        exclude_nonEnglish=True))

            cache.set(key_all, all_films, cache.A_MONTH)

        # Select random few films
        random.shuffle(all_films)
        films = all_films[:films_number]
        cache.set(key, films, cache.A_QUARTER)

    return films[:films_number]

@register.inclusion_tag('home/top_on_main_page.html', takes_context=True)
def top_on_main_page(context):

    POPULAR_FILMS_NUMBER = getattr(settings,
            'POPULAR_FILMS_MAIN_PAGE_NUMBER')
    CINEMA_FILMS_NUMBER = getattr(settings,
            'CINEMA_FILMS_MAIN_PAGE_NUMBER')
    TV_FILMS_NUMBER = getattr(settings,
            'TV_FILMS_MAIN_PAGE_NUMBER')

    recommendations_user = context.get( 'recommendations_user', False ) 
    user = recommendations_user or context['request'].user

    all_films_number = POPULAR_FILMS_NUMBER

    cinema_films = top_recommendations_cinema(context,
            CINEMA_FILMS_NUMBER)
    if len(cinema_films) < CINEMA_FILMS_NUMBER:
        all_films_number +=  CINEMA_FILMS_NUMBER
        cinema_films = None

    tv_films = top_recommendations_tv(context, TV_FILMS_NUMBER)
    if len(tv_films) < TV_FILMS_NUMBER:
        all_films_number += TV_FILMS_NUMBER
        tv_films = None

    all_films = top_recommendations_all(context, all_films_number)

    return{
        'cinema_films': cinema_films,
        'tv_films': tv_films,
        'all_films': all_films,
        'is_authenticated': recommendations_user or user.is_authenticated(),
        'show_links': not recommendations_user,
    }


@register.inclusion_tag('widgets/random_top_movie.html')
def random_top_movie():
    """Displays some random popular movie on Filmaster."""

    key = cache.Key("popular_films")
    popular_films = cache.get(key)
    if popular_films is None:
        # Get most popular films
        fhelper = FilmHelper()
        popular_films = list(fhelper.get_popular_films(
            exclude_nonEnglish=True))
        cache.set(key, popular_films)
    random.shuffle(popular_films)
    if len(popular_films) > 0:
        return {'movie': popular_films[0]}
    else:
        return {'movie': None}

@register.inclusion_tag('profile/right_sidebar/users_best_rated.html')
def users_best_rated(user):
    """Displays user's top rated movies."""

    cache_key = cache.Key("profile_page_best_films", user)
    best_movies = cache.get(cache_key)
    NUMBER_OF_USER_BEST_FILMS = \
            getattr(settings, 'NUMBER_OF_USER_BEST_FILMS')
    
    if not best_movies:
        fhelper = FilmHelper()
        best_movies = fhelper.get_users_best_films(user,
                NUMBER_OF_USER_BEST_FILMS + 1)
        cache.set(cache_key, best_movies)

    show_more = len( best_movies ) == NUMBER_OF_USER_BEST_FILMS + 1
    best_movies = best_movies[:NUMBER_OF_USER_BEST_FILMS]

    return {'movies': best_movies, 'show_more': show_more, 'act_user': user }

@register.inclusion_tag('profile/right_sidebar/wishlist.html')
def users_wishlist(user):
    """ Displays on sidebar, movies user want to watch."""

    key = cache.Key("user_wishlist_sidebar", user)
    movies = cache.get(key)
    NUMBER_OF_MOVIES_WISHLIST_SIDEBAR = \
            getattr(settings, 'NUMBER_OF_MOVIES_WISHLIST_SIDEBAR')
    
    if not movies:
        movies = [item.film for item in BasketItem.objects.filter(user=user,
                wishlist=BasketItem.DYING_FOR)\
                [:NUMBER_OF_MOVIES_WISHLIST_SIDEBAR + 1]]
        cache.set(key, movies, 3 * cache.CACHE_HOUR)

    show_more = len( movies ) == NUMBER_OF_MOVIES_WISHLIST_SIDEBAR + 1
    movies = movies[:NUMBER_OF_MOVIES_WISHLIST_SIDEBAR]

    return {'movies': movies, 'show_more': show_more, 'act_user': user }

@register.inclusion_tag('profile/right_sidebar/shitlist.html')
def users_shitlist(user):
    """ Displays on sidebar, movies user doesn't want to watch."""

    key = cache.Key("user_shitlist_sidebar", user)
    movies = cache.get(key)
    NUMBER_OF_MOVIES_SHITLIST_SIDEBAR = \
            getattr(settings, 'NUMBER_OF_MOVIES_SHITLIST_SIDEBAR')

    if not movies:
        movies = [item.film for item in BasketItem.objects.filter(user=user,
                wishlist=BasketItem.NOT_INTERESTED)\
                [:NUMBER_OF_MOVIES_SHITLIST_SIDEBAR + 1]]
        cache.set(key, movies, 3 * cache.CACHE_HOUR)

    show_more = len( movies ) == NUMBER_OF_MOVIES_SHITLIST_SIDEBAR + 1
    movies = movies[:NUMBER_OF_MOVIES_SHITLIST_SIDEBAR]

    return {'movies': movies, 'show_more': show_more, 'act_user': user }

@register.widget('movies/rating/single_film_form.html')
def random_film_to_rate(request):
    """
        Widget for main page (for not logged in users)
        displaying a film to rate, selected from
        the list of 10 most popular films.
    """

    user = request.user
    
    if user.is_authenticated():
        film = Film.get_next_film_to_rate(user)
    else:
        key = cache.Key("popular_films_list")

        popular_films = cache.get(key)

        if popular_films is None:
            fhelper = FilmHelper()
            lang = getattr(settings, 'LANGUAGE_CODE', 'en')
            if lang == 'en':
                popular_films = fhelper.get_popular_films(exclude_nonEnglish=True)
            else:
                popular_films = fhelper.get_popular_films()
            cache.set(key, popular_films)

        film = popular_films and random.choice(popular_films) or None

    return {
        'film': film, 
    }

@register.simple_tag(takes_context=True)
def next_film_to_rate_url(context, user):
    request = context['request']
    if settings.NEW_RATING_SYSTEM:
        rater = rating_helper.get_rater(request)
        films = rater.get_films_to_rate(1)
        film = films and films[0] or None
    else:
        film = Film.get_next_film_to_rate(user)
    
    if film:
        return film.get_absolute_path()
    else:
        return ''


@register.inclusion_tag('widgets/short_reviews.html', takes_context=True)
def short_reviews(context, limit=10, param=None, argument=None):
    """
        Configurable widget displaying short reviews
        Takes te following arguments:
        - list of films (can be none), param is "films" and argument is a
        list of film objects
        - film genre (can be none), param is genre and argument is a
        string with film genre
        - if both are none it displays recent last month hand-selected reviews
    """
    request = context['request']
    key = "short_reviews"
    key_params = "short_reviews_params"
    key_films = "films_for_tag"

    if param == "films":
        if argument:
            key += "_".join(film.permalink for film in argument if film and film.pk)

    films = cache.get_cache(CACHE_ACTIVITIES, key_films)
    if param == 'genre':
        if not films:
            rh = RecomHelper()
            films = rh.get_films_for_tag(argument, limit=500, order_by="-popularity")
            key_films += "_".join(film.permalink for film in films if film and film.pk)
            cache.set_cache(CACHE_ACTIVITIES, key_films, films)


    # -- check if path contains tags --
    request_tags = request.GET.get("tags", "")
    request_path = request.META.get("PATH_INFO", "")

    if urls['TAG'] in request_path.lower():
        request_path = request_path.strip(urls['TAG'])
    else:
        request_path = ""

    if param == "genre":
        if request_tags:
            argument = request_tags
        if request_path:
            argument = request_path
        key += "_%s" % argument

    query = cache.get_cache(CACHE_ACTIVITIES, key)
    params = cache.get_cache(CACHE_ACTIVITIES, query)

    if not query:
        params = True
        if param == "films":
            query = UserActivity.objects.select_related('user', 'film', 'short_review').filter(
                activity_type = UserActivity.TYPE_SHORT_REVIEW,
                film__in = argument,
                #featured = True,
                ).order_by("-created_at")[:limit]

        if param == "genre":
            query = UserActivity.objects.select_related('user', 'film', 'short_review').filter(
                activity_type = UserActivity.TYPE_SHORT_REVIEW,
                film__in = films,
                #featured = True,
                ).order_by("-created_at")[:limit]

        if not query:
            params = False
            query = UserActivity.objects.select_related('user', 'film', 'short_review').filter(
                activity_type = UserActivity.TYPE_SHORT_REVIEW,
                #featured = True,
                ).order_by("-created_at")[:limit]

        query = list(query)
        random.shuffle(query)
        cache.set_cache(CACHE_ACTIVITIES, key, query, CACHE_HOUR * 3)
        cache.set_cache(CACHE_ACTIVITIES, query, params, CACHE_HOUR * 3)

    return {'activities': query, 'params': params}

@register.inclusion_tag('widgets/movies_slider_widget.html')
def show_movies_slider_widget(limit=settings.NUMBER_OF_MOVIES_FOR_WIDGET):
    CACHE_RANDOM_FILMS = 'random_films_for_tag'
    CACHE_FILMS_FOR_TAG = 'films_for_tag'
    CACHE_LINKS_FOR_GENRE = 'links_for_genre'

    tags = Film.get_top_tags()
    key = 'tag'
    key += "_".join(str(tag.id) for tag in tags)

    films_for_tags = cache.get_cache(CACHE_FILMS_FOR_TAG, key)
    films_list = cache.get_cache(CACHE_RANDOM_FILMS, films_for_tags)
    if not films_list:
        films_list = []
        if not films_for_tags:
            films_for_tags = []
            for tag in tags:
                rh = RecomHelper()
                films = rh.get_films_for_tag(str(tag), order_by="-popularity")
                films = films.filter(image__isnull = False)
                films_for_tags.append(films[:100])
            cache.set_cache(CACHE_FILMS_FOR_TAG, key, films_for_tags)

        for films in films_for_tags:
            films = list(films)
            random.shuffle(films)
            films = films[:limit]
            films_list += films
        cache.set_cache(CACHE_RANDOM_FILMS, films_for_tags, films_list, CACHE_HOUR)

    links_list = cache.get_cache(CACHE_LINKS_FOR_GENRE, key)
    if not links_list:
        links_list = []
        for tag in tags:
            links = reverse('movies_menu', args=(tag.name,))
            links_list.append(links)
        cache.set_cache(CACHE_LINKS_FOR_GENRE, key, links_list)

    return {'films':films_list, 'tags': tags, 'links': links_list}

@register.widget('movies/movie/checkin.html', lambda film:dict(film_id=film.id))
def film_checkin(request, film=None):
    film = film or get_object_or_404(Film, id=request.GET.get('film_id'))
    if request.user.is_authenticated():
        checkin = film.last_check_in(request.user)
        checkin = checkin if checkin and checkin.status == 1 else None
    else:
        checkin = None
    return {
        'checkin':checkin,
        'film_uri': '/1.1/film/%s/' % film.permalink,
    }

@register.widget('movies/movie/checkin.html', lambda screening:dict(screening_id=screening.id))
def screening_checkin(request, screening=None):
    screening_id = screening and screening.pk or request.GET.get('screening_id')
    checkin = None
    if request.user.is_authenticated():
        try:
            checkin = ScreeningCheckIn.objects.get(screening=screening_id, user=request.user, status=1)
        except ScreeningCheckIn.DoesNotExist, e:
            pass
    return {
        'checkin':checkin,
        'screening_uri': '/1.1/screening/%s/' % screening_id,
    }

@register.filter
def release_date(film, country_code=None):
    return film.get_release_date(country_code)
