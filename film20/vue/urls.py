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
from film20.config.urls import *
urlpatterns = patterns('film20.vue.views',
    url(r'^$','main', name="vue_main"),
    url(r'^ajax/rated/$', 'ajax_rated'),
    url(r'^ajax/recommendations/(?P<kind>(all|vue))/$', 'ajax_recommendations'),
    url(r'^film/(?P<id>\d+)/$', 'film_details', name='vue_film_details'),
    url(r'^recommendations/$', 'detailed_recommendations_vue', name="detailed_recommendations_vue"),
    url(r'^recommendations/all/$', 'detailed_recommendations_all', name="detailed_recommendations_all"),
    url(r'^ajax/process-vote/$', 'process_vote', name='vue_process_vote'),
)
