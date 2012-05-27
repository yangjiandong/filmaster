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

urlpatterns = patterns('film20.fbapp.views',
# Removed as we don't support festivals yet in new version
    url(r'^$', 'fbapp', name='fbapp'),
    url(r'^main/$', 'main', name='fbapp_main'),
    url(r'^login_or_signup/$', 'login_or_signup', name='fbapp_login_or_signup'),
    url(r'^viral/$', 'viral_view', name='fbapp_viral_view'),
    url(r'^the_end/$', 'the_end', name='fbapp_the_end'),
    url(r'^quiz/$', 'quiz', name='fbapp_quiz'),
    url(r'^ticket/$', 'choose_ticket', name='fbapp_choose_ticket'),
    url(r'^rate_films/$', 'rate_films', name='fbapp_rate_films'),
    url(r'^terms/$', 'terms', name='fbapp_terms'),
    url(r'^contact/$', 'contact', name='fbapp_contact'),
    url(r'^results/$', 'results', name='fbapp_results'),
    url(r'^results/(?P<pk>\d+)/$', 'results', name='fbapp_results'),
    # events
    url(r'^(?P<slug>[\w\-_]+)/$', 'event', name='event'),
    url(r'^(?P<slug>[\w\-_]+)/quiz/$', 'event_quiz', name='event_quiz'),
    url(r'^(?P<slug>[\w\-_]+)/rate_films/$', 'event_rate_films', name='event_rate_films'),
    url(r'^(?P<slug>[\w\-_]+)/viral/$', 'event_viral', name='event_viral'),
    url(r'^(?P<slug>[\w\-_]+)/score_board/$', 'event_score_board', name='event_score_board'),
)
