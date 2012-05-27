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
from film20.config.urls import *
from film20.recommendations.views import *

ranking_view = RankingListView.as_view()
recommendations_view = RecommendationsListView.as_view()

genre = r"/(?P<genre>.+)/$"

recompatterns = patterns('',
                      
    ### RANKING ###
    url(r'^%(RANKING)s/$' % urls, ranking_view, name='rankings'),
    url(r"^%(RANKING)s/(?P<type_as_str>['\w\-_]+)/$" % urls, ranking_view, name='rankings'),
    url(r'^%(RANKING)s/%(GENRE)s' % urls + genre, ranking_view, name='rankings_menu'),
    url(r'^%(TV_SERIES_RANKING)s/$' % urls, ranking_view, {'tv_series': True}, name='series_rankings'),
    url(r"^%(TV_SERIES_RANKING)s/(?P<type_as_str>['\w\-_]+)/$" % urls, ranking_view, {'tv_series': True}, name='series_rankings'),
    url(r'^%(TV_SERIES_RANKING)s/%(GENRE)s' % urls + genre, ranking_view, {'tv_series': True}, name='series_rankings_menu'),

    url(r'^'+urls['MOVIES']+'/$', MoviesMainListView.as_view(), name='movies'),
    url(r'^'+urls['MOVIES']+'/'+urls['GENRE']+ genre, MoviesGenreListView.as_view(), name='movies_menu'),

    url(r'^'+urls['REVIEWS']+'/$', ReviewsListView.as_view(), name='reviews'),
    url(r'^'+urls['REVIEWS']+'/(?P<notes_type>[\w\-_]+)/$', login_required(ReviewsListView.as_view()), name='reviews'),
    url(r'^'+urls['REVIEWS']+'/'+urls['GENRE']+ genre, ReviewsListView.as_view(), name='reviews_menu'),

    url(r'^'+urls["RECOMMENDATIONS"]+'/$', recommendations_view, name='my_recommendations'),
    url(r'^'+urls["RECOMMENDATIONS"] + "/" + urls["GENRE"] + genre, recommendations_view, name='recommendations_menu'),

# These are old views, not (yet) implemented in filmaster-reloaded

    ### TOP USERS ###
#    (r'^'+urls["TOP_USERS"]+'/$', top_users),
#    (r'^'+urls["TOP_USERS"]+'/(?P<page_id>\d{1,3})/$', top_users),

	### TAG PAGE ###
    url(r'^'+urls['SHOW_TAG_PAGE']+ genre, MoviesGenreListView.as_view(), name='show_tag_page'),

    ### FILMS FOR TAG ###
#    (r'^'+urls['SHOW_TAG_PAGE']+'/(?P<tag>[\w\-_ ]+)/'+urls['FILMS_FOR_TAG']+'/$', show_films_for_tag),
#    (r'^'+urls['SHOW_TAG_PAGE']+'/(?P<tag>[\w\-_ ]+)/'+urls['FILMS_FOR_TAG']+'/(?P<page_id>\d{1,3})/$', show_films_for_tag),
)
