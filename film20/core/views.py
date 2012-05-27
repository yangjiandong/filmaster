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
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader
from django import forms
from django.views.decorators.cache import never_cache
from django.http import Http404
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from film20.config.urls import *
from film20.utils.utils import *
from film20.core.film_helper import FilmHelper
from film20.core.search_helper import SearchForm
from film20.blog.models import Post
from django.conf import settings
from film20.core.rating_form import FilmRatingForm, SingleRatingForm
from film20.core.models import Film, Person, Object
from film20.useractivity.models import UserActivity
from film20.dashboard.forms import WallForm
from django.contrib import messages


RECOMMENDED_USERS = settings.RECOMMENDED_USERS

import logging
logger = logging.getLogger(__name__)

import film20.settings as settings

# constants
NUMBER_OF_REVIEWS_FRONT_PAGE = getattr(settings, "NUMBER_OF_REVIEWS_FRONT_PAGE", 9)

def show_main(request, tag=None):
    search_form = SearchForm()
    
    response = render_to_response(
        templates['MAIN'],
        {
            'search_form' : search_form,
        },
        context_instance=RequestContext(request),
    )
    return response

from film20.pagination.paginator import InfinitePaginator
from django.views.generic.list import ListView
class PaginatorListView(ListView):
    list_of_pages = False
    is_showing_all = False
    show_all = False
    page_size = 20
    adjacent_pages = 3
    
    @property
    def paginate_by(self):
        paginate_by = self.page_size
        if self.show_all:
            if 'show_all' in self.request.GET:
                paginate_by = None
                self.is_showing_all = True
        return paginate_by

    def get_params(self):
        self.has_args = False
        self.args = ""

        page_key = 'page'
        params = self.request.GET.copy()
        if params:
            self.has_args = True
            if page_key in params:
                del params[page_key]
            self.args = params.urlencode()

    def get_context_data(self, **kwargs):
        self.get_params()
        context = super(PaginatorListView, self).get_context_data(**kwargs)

        page_numbers = 0
        if not self.is_showing_all:
            paginator=context['paginator']
            try:
                current_page = int(self.request.GET.get('page'))
            except:
                current_page = 1
            if self.list_of_pages:
                page_numbers = [n for n in \
                    range(current_page - self.adjacent_pages, current_page + self.adjacent_pages + 1) \
                    if n > 0 and n <= paginator.num_pages]
            else:
                page_numbers = [current_page]

        context['is_showing_all'] = self.is_showing_all
        context['show_all'] = self.show_all
        context['has_args'] = self.has_args
        context['args'] = self.args
        context['list_of_pages'] = self.list_of_pages
        context['page_size'] = self.page_size
        context['page_numbers'] = page_numbers
        return context

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        if self.list_of_pages:
            paginator_class = self.paginator_class
        else:
            paginator_class = InfinitePaginator
        return paginator_class(queryset, per_page, orphans=orphans, allow_empty_first_page=allow_empty_first_page)


class UsernameMixin(object):
    def get_username(self, **kwargs):
        self.user = None
        self.user_profile = None
        if 'username' in self.kwargs:
            try:
                username = self.kwargs['username']
                self.user = User.objects.get(username__iexact=username, is_active=True)
                self.user_profile = self.user
            except User.DoesNotExist:
                # sanity check for params (http://jira.filmaster.org/browse/FLM-97)
                raise Http404
        else:
            self.user = self.request.user

    def get_context_data(self, **kwargs):
        if not hasattr(self, 'user_profile'):
            self.get_username()
        context = super(UsernameMixin, self).get_context_data(**kwargs)
        context['user_profile'] = self.user_profile
        return context

class BetaForm(forms.Form):
    beta_code = forms.CharField(label=_("Beta code"), max_length=10, widget=forms.TextInput({'class':'text'}),)
    def clean_beta_code(self):
        beta_code = self.cleaned_data.get('beta_code', '')
        if beta_code:
            # empty is not good
            if beta_code!='rosebud':
                raise forms.ValidationError(_("Sorry but this is not the correct passphrase!"))
            else:
                return beta_code
        else:
            return None

def show_beta(request):
    beta_form = BetaForm()
    if request.POST:
        beta_form = BetaForm(request.POST)
        if beta_form.is_valid():
           request.session["in_beta"] = True
           return HttpResponseRedirect("/access-granted/")
        else:
           try:
                request.session["beta_no_of_tries"] = request.session["beta_no_of_tries"]+1
           except:
                request.session["beta_no_of_tries"] = 1
    try:
        tries = request.session["beta_no_of_tries"]
        if tries==1:
            hint = "It's a phrase that was crucial to a major American movie..."
        elif tries==2:
            hint = "The movie was made before 1990"
        elif tries==3:
            hint = "Actually it was made even before 1970"
        elif tries==4:
            hint = "OK, it was made in the fourties"
        elif ( (tries>4) & (tries<8) ):
            hint = "The movie directed by a guy with initials: O.W. Now you gotta know!"
        else:
            hint = "All right... if you are giving up, just register at filmaster.com, fill in the beta-tester form and beg for the access. We may be merciful, who knows..."
    except:
        hint = None

    return render_to_response(
        "beta.html",
        {
            'beta_form' : beta_form,
            'hint': hint,
        }, 
        context_instance=RequestContext(request),
    )

def access_granted(request):
    return render_to_response(
        "access_granted.html",
        {
        }, 
        context_instance=RequestContext(request),
    )
 
@never_cache
def ping(request):
    # do some db query
    User.objects.all()[0]
    return HttpResponse('pong')

def create_handler(status):
    def handler(request):
        if getattr(request, '_api', False):
            response = "Error %d" % status
        elif request.path_info.startswith('/vue/'):
            t = loader.get_template("vue/%d.html" % status)
            response = t.render(RequestContext(request))
        else:
            t = loader.get_template("%d.html" % status)
            response = t.render(RequestContext(request))
        return HttpResponse(response, status=status)
    return handler

from film20.core import rating_helper
def rate_film(request):
    if request.method != 'POST':
        return HttpResponse("bad request", status=400)
    from film20.core.models import Rating
    if not request.user.is_authenticated():
        request.user.session_key = request.session.session_key
    if 'film_id' in request.POST:
        film = get_object_or_404(Film, id=request.POST['film_id'])
    elif 'film_permalink' in request.POST:
        film = get_object_or_404(Film, permalink=request.POST['film_permalink'])
    else:
        return HttpResponse("Bad Request", status=400)

    try:
        value = request.POST.get('rating') or None
        if value:
            value = max(1, min(10, int(value)))
    except ValueError, e:
        value = None

    if not value and not request.unique_user.id:
        return HttpResponse("Bad Request", status=400)

    type = int(request.POST.get('type', 1))

    rater = rating_helper.get_rater(request)
    rater.rate_film(film.id, value, type)

    return HttpResponse('')

def process_ratings(request):
    data = request.POST

    if not data:
        data = request.session.get('rating_data')
        logger.info("RATING DATA FROM SESSION: %r", data)
        if data:
            del request.session['rating_data']
    if data:
        form_prefixes = FilmRatingForm.get_form_prefixes(data)
        for prefix in form_prefixes:
            film_id = prefix[4:]
            film = get_object_or_404(Film, id=film_id)
            form = FilmRatingForm(data, request, film)
            if form.is_valid():
                form.save()

        form_prefixes = SingleRatingForm.get_form_prefixes(data)
        for prefix in form_prefixes:
            form = SingleRatingForm(data, request, prefix=prefix)
            if form.is_valid():
                form.save()
            else:
                errors = form.errors
                assert 0
    
    next = data and data.get('next')
    if not next:
        if request.is_ajax():
            return HttpResponse('ok')
        try:
            referer = request.META['HTTP_REFERER']
        except:
            referer = ''

        if urls['WISHLIST'] in referer:
            next = reverse('wishlist')
        elif urls['SHITLIST'] in referer:
            next = reverse('shitlist')
        elif urls['OWNED'] in referer:
            next = reverse('collection')
        elif referer:
            next = referer
        else:
            next = reverse('main_page')

    return HttpResponseRedirect(next)

@json_response
def recommendations_status(request):
    user = request.unique_user
    if user.id:
        profile = user.get_profile()
        status = profile.recommendations_status
    else:
        status = 0
    return {
        'recommendations_status':status
    }
    
@never_cache
def ajax_widget(request, library, name):
    from django.template import get_library
    lib = get_library(library)
    resp = lib.get_widget_view(name)(request)
    try:
        from djangologging import SUPPRESS_OUTPUT_ATTR
        setattr(resp, SUPPRESS_OUTPUT_ATTR, True)
    except ImportError:
        pass
    return resp

handler500 = create_handler(500)
handler404 = create_handler(404)
