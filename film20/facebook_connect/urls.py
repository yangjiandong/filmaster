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
import django.contrib.auth.views
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('film20.facebook_connect.views',
url(r'^$', 'show_login'),
url(r'^begin/$',  'fb_begin', name='fb_begin'),
url(r'^auth-cb/$', 'fb_auth_cb', name='fb_auth_cb'),
url(r'^new/$', 'fb_register_user', name='fb_register_user'),
url(r'^assign/$', 'assign_facebook', name='fb_assign'),
url(r'^error/$', 'fb_error'),
url(r'^unassign/$', 'unassign_facebook', name='facebook_unassign'),
url(r'^store-request/$', 'store_request', name='store_request'),
)
root_urlpatterns = patterns('film20.facebook_connect.views',
    url(r'^ajax/fb/like/$', 'fb_like', name='fb_like'),
)

