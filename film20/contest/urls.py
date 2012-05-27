#-------------------------------------------------------------------------------
# Filmaster - a social web network and recommendation engine
# Copyright (c) 2010 Filmaster (Borys Musielak, Adam Zielinski).
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
from film20.contest.views import show_game, show_contest, show_game_ajax

contestpatterns = patterns('',
    # specific contest
    (r'^'+urls['SHOW_CONTEST']+'/(?P<contest_permalink>[\w\-_]+)?/$', show_contest),

    # current game in specific contest
    (r'^'+urls['SHOW_CONTEST']+'/(?P<contest_permalink>[\w\-_]+)/'+urls['SHOW_GAME']+'?/$', show_game),
    (r'^'+urls['SHOW_CONTEST']+'/(?P<contest_permalink>[\w\-_]+)/'+urls['SHOW_GAME']+'?/(?P<ajax>json|xml)/$', show_game),

    # specific game in contest
    (r'^'+urls['SHOW_CONTEST']+'/(?P<contest_permalink>[\w\-_]+)/'+urls['SHOW_GAME']+'/(?P<game_permalink>[\w\-_]+)?/$', show_game),
    (r'^'+urls['SHOW_CONTEST']+'/(?P<contest_permalink>[\w\-_]+)/'+urls['SHOW_GAME']+'/(?P<game_permalink>[\w\-_]+)?/(?P<ajax>json|xml)/$', show_game),
    (r'^'+urls['CONTEST_VOTE_AJAX']+'/(?P<user_id>[\d]+)/$', show_game_ajax),
)
