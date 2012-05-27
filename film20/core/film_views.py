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
import random

from django.utils.translation import gettext_lazy as _, gettext
from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db.models import Q
from django import forms
from django.views.decorators.cache import never_cache

from django.utils import simplejson
from django.core.urlresolvers import reverse

from film20.config.urls import *
from film20.utils.utils import *
from film20.core.models import Object
from film20.core.models import Film
from film20.core.models import Rating, Character
from django.contrib.auth.models import User
from film20.core.models import Profile
from film20.core.film_helper import FilmHelper
from film20.core.rating_form import RatingForm
from film20.core import rating_helper
from film20.tagging.models import TaggedItem
from film20.core.models import FilmLocalized
from film20.core.models import ObjectLocalized
from film20.blog.models import Post
from film20.recommendations.recom_helper import RecomHelper
from film20.filmbasket.forms import ButtonsForm
from film20.shop.shop_helper import ShopHelper

import logging
logger = logging.getLogger(__name__)

TAGGING_FORM_ID = "876"
LOCALIZED_TITLE_FORM_ID = "877"
DESCRIPTION_FORM_ID = "878"
SHORT_REVIEW_FORM_ID = "879"

from django.conf import settings

# constants
MAX_ACTORS = getattr(settings, "MAX_ACTORS", 15)
NUMBER_OF_RELATED_FILMS = getattr(settings, "NUMBER_OF_RELATED_FILMS", 6)

from django.shortcuts import get_object_or_404

from film20.core.models import ShortReview
from film20.useractivity.models import UserActivity
from film20.dashboard.forms import WallForm
from django.contrib import messages

from film20.useractivity.views import WallView

class ShowFilmView(WallView):
    template_name = 'movies/movie.html'

    def get_object(self):
        film = get_object_or_404(Film.objects.cache(), permalink=self.kwargs['permalink'])
        if ('tv_series' in self.kwargs) ^ film.is_tv_series:
            raise Http404()
        film.parent = Object(id=film.parent_id)
        return film

    def get_activities(self):
        return UserActivity.objects.filter(film=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super(ShowFilmView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            from film20.filmbasket.models import BasketItem
            user = self.request.user
            BasketItem.user_basket(user)
            film = self.get_object()
            try:
                basket = user._basket[film.id]
                owned = basket[1]
            except:
                owned = None
            context['user_film_basket'] = owned
        return context

show_film = ShowFilmView.as_view()
 
class ShowFilmRatings(WallView):
    template_name = 'movies/all_ratings.html'
    context_object_name = "movie_ratings"
    
    def get_object(self):
        film = get_object_or_404(Film.objects.cache(), permalink=self.kwargs['permalink'])
        film.parent = Object(id=film.parent_id)
        return film

    def get_queryset(self):
        film = self.get_object()
        show_key = 'show'
        params = self.request.GET.copy()
        ratings = film.get_ratings()
        if self.request.user.is_authenticated:
            if show_key in params:
                if params[show_key] == 'friends':
                    ratings = film.get_friends_ratings(self.request.user)
                elif params[show_key] == 'similar':
                    ratings = film.get_similar_users_ratings(self.request.user, 100)
                else:
                    ratings = []
        return ratings
       
def mark_prev_films_as_seen(request):
    prev_film_ids = request.POST.get('prev_film_ids')
    if prev_film_ids:
        if not request.unique_user.is_authenticated():
            request.unique_user.make_unique()
        prev_film_ids = map(int, prev_film_ids.split(','))
        rater = rating_helper.get_rater(request)
        rater.mark_films_as_seen(prev_film_ids)

@login_required
def ajax_film_ratings_form(request, permalink):
    mark_prev_films_as_seen(request)
    
    film = get_object_or_404(Film, permalink=permalink)
    
    context = {
        'film': film,
    }
    return render(request, 'movies/rating/ajax_ratings_form.html', context)

@login_required
def next_film_to_rate(request):
    film = Film.get_next_film_to_rate(request.user)
    if film:
        return HttpResponseRedirect(film.get_absolute_url())
    else:
        return render(request, "movies/no_more_to_rate.html")

@never_cache
def rate_films(request, tag=None):
    if not request.user.is_authenticated():
        request.unique_user.make_unique()
    mark_prev_films_as_seen(request)

    try:
        films_nr = int(request.GET.get('films_nr', 0))
    except ValueError, e:
        pass
    films_nr = films_nr or settings.RATING_FILMS_NUMBER

    if settings.NEW_RATING_SYSTEM:
        rater = rating_helper.get_rater(request)
        films = rater.get_films_to_rate(films_nr, tag)
    else:
        films = Film.get_films_to_rate(user, films_nr, tag)

    if 'ajax' in request.GET:
        template = "movies/rate_movies_ajax.html"
    else:
        template = "movies/rate_movies.html"
    response = render(request, template, {
        'films':films or [],
        'tag':tag,
        'rater': request.GET.get('rater'),
    })
    return response

@never_cache
def rate_next_film(request, tag=None):
    mark_prev_films_as_seen(request)

    if settings.NEW_RATING_SYSTEM:
        rater = rating_helper.get_rater(request)
        films = rater.get_films_to_rate(1, tag)
    else:
        films = Film.get_films_to_rate(user, 1, tag)

    return render(request, "movies/rating/single_film_special.html", {
        'film': films[0] if len( films ) else None,
        'tag':tag,
        'rater':request.GET.get('rater'),
    })



from film20.core.models import ModeratedFilmLocalized

@login_required
def edit_film_localized_data( request, permalink, type ):
    allowed_types = [ 'title', 'description', 'tags' ]

    film = get_object_or_404( Film, permalink=permalink )
    def get_title():
        f = Film.objects.get( pk=film.pk )
        return f.get_localized_title()

    def get_description():
        f = Film.objects.get( pk=film.pk )
        return f.get_description()

    def get_tags():
        f = Film.objects.get( pk=film.pk )
        return filter( bool, ( t.strip() for t in f.get_tags().split( ',' ) ) )

    result = { 'success': True }
    if type in allowed_types:
        if request.method == 'POST':
            v = request.POST['value']
            perm = request.user.has_perm( 'core.can_accept_localized_data' )
            if not perm:
                mf = ModeratedFilmLocalized.objects.create( film=film, user=request.user )

            if type == 'title':
                if perm:
                    film.save_localized_title( v )
                else:
                    mf.title = v 
                v = get_title()
        
            if type == 'description':
                if perm:
                    film.save_description( v )
                else:
                    mf.description = v
                v = get_description()
        
            if type == 'tags':
                if perm:
                    film.save_tags( v )
                else:
                    mf.tag_list = v
                v = get_tags()
        
            if not perm:
                result[ 'need_moderate' ] = True
                result[ 'message' ] = str( _( 'Element saved! awaiting approval' ) )
                mf.save()

            else:
                result['message'] = str( _( 'Element saved!' ) )

            result['value'] = v
        
        elif request.method == 'GET':
            if type == 'title':
                v = get_title()

            if type == 'description':
                v = get_description()

            elif type == 'tags':
                v = ', '.join( get_tags() )

            result['value'] = v
        else:
            raise AttributeError
    else:
        raise AttributeError

    return HttpResponse( simplejson.dumps( result ), mimetype="application/json" )
