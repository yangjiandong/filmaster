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
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from film20.core.views import *
from film20.core.film_views import *
from film20.core.person_views import *
from django.views.generic.simple import direct_to_template

corepatterns = patterns('',

    ### Main page ###
    url(r'^$', show_main, name='main_page'),
    
    ### Film view ###
#    url(r'^%(FILM)s/(?P<permalink>[\w\-_]+)/$' % urls, show_film, name='show_film'),
    url(r'^%(FILM)s/(?P<permalink>[\w\-_]+)/$' % urls, ShowFilmView.as_view(), name='show_film'),
    url(r'^%(TV_SERIES)s/(?P<permalink>[\w\-_]+)/$' % urls, ShowFilmView.as_view(), {'tv_series': True}, name='show_series'),
    url(r'^%(FILM)s/(?P<permalink>[\w\-_]+)/%(RATINGS)s/$' % urls, ShowFilmRatings.as_view(), name='show_film_all_ratings'),
    url(r'^%(FILM)s/(?P<permalink>[\w\-_]+)/ajax-rating/$' % urls, ajax_film_ratings_form),
    url(r'^%(FILM)s/(?P<permalink>[\w\-_]+)/login/$' % urls, login_required(ShowFilmView.as_view()), name='show_film_login'),

    # edit localized data
    url(r'^%(FILM)s/(?P<permalink>[\w\-_]+)/edit/(?P<type>[\w\-_]+)/$' % urls, edit_film_localized_data , name='edit-localized'),
    url(r'^%(TV_SERIES)s/(?P<permalink>[\w\-_]+)/edit/(?P<type>[\w\-_]+)/$' % urls, edit_film_localized_data , name='edit-localized'),
    url(r'^%(PERSON)s/(?P<permalink>[\w\-_]+)/edit/(?P<type>[\w\-_]+)/$' % urls, edit_person_localized_data , name='edit-localized'),

    ### Rate films views ###
    url(r'^%(RATE_FILMS)s/$' % urls, rate_films, name='rate_films'),
    url(r'^%(RATE_FILMS)s/(?P<tag>[^/]+)/$' % urls, rate_films, name='rate_films'),
    
    url(r'^%(RATE_NEXT)s/$' % urls, next_film_to_rate, name='next_film_to_rate'),
    
    ### Person view ###
#    url(r'^%(PERSON)s/(?P<permalink>[\w\-_]+)/$' % urls, show_person, name='show_person'),
    url(r'^%(PERSON)s/(?P<permalink>[\w\-_]+)/$' % urls, ShowPersonView.as_view(), name='show_person'),
    url(r'^ajax/process-ratings/$', 'film20.core.views.process_ratings', name='process_ratings'),
    url(r'^ajax/rate-film/$', 'film20.core.views.rate_film', name='rate_film'),
    url(r'^ajax/rate-next/$', rate_next_film, name='rate_next_film'),
    url(r'^ajax/recommendations-status/$', 'film20.core.views.recommendations_status'),

    url(r'^ajax/compare-films/$', 'film20.film_features.views.compare_films', name='compare-films' ),
    url(r'^ajax/compare-films/(?P<id>\d+)/$', 'film20.film_features.views.compare_films', name='compare-films' ),
    url(r'^ajax/widget/([\w_\.]+)/([\w_]+)/$', 'film20.core.views.ajax_widget', name='ajax_widget'),
)
