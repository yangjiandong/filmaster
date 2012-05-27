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
from film20.recommendations.views import *
from film20.festivals.views import *

urlpatterns = patterns('film20.festivals.views',
# Removed as we don't support festivals yet in new version
    url(r'^$', 'show_festival', name='show_festival'),
    url(r'^%(RECOMMENDATIONS)s/$' % urls, 'festival_recommendations', name='festival_recommendations'),
    url(r'^%(AGENDA)s/(?P<date>\d\d\d\d-\d\d-\d\d)/$' % urls, 'festival_agenda', name='festival_agenda'),
    url(r'^%(FILMS)s/$' % urls, 'festival_films', name='festival_films'),
    url(r'^%(FILMS)s/%(ORIGINAL_TITLE)s/$' % urls, 'festival_films', {'order_by':'original_title'}, name='festival_films_by_orig_title'),
    url(r'^%(REVIEWS)s/$' % urls, 'festival_reviews', name='festival_reviews'),
    url(r'^%(FESTIVAL_RANKING)s/$' % urls, 'festival_ranking', name='festival_ranking'),
    # listed festivals by name
    # TODO: think of how to automate this - perhaps get from database (festival table)
    # first time and then get them from memcached?
#    (r'^(?P<permalink>enh|ENH|wff|piec-smakow|lff|sputnik|filmy-swiata|alekino|tofifest)/$', show_festival),
)
