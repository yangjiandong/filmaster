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

from film20.posters.models import ModeratedPhoto, moderated_photo_item
from film20.posters.views import add_photo, image

from film20.moderation.views import moderate_item, get_feed

posterpatterns = patterns( '',   
    url( r'^%s/rss/$' % urls['POSTER_ADD'], get_feed, { 'model': moderated_photo_item.get_name(), 'status': ModeratedPhoto.STATUS_ACCEPTED } ),
    url( r'^%s/admin/$' % urls['POSTER_ADD'], moderate_item, { 'model': moderated_photo_item.get_name() }, name='poster-admin' ),
    url( r'^%s/admin/rss/$' % urls['POSTER_ADD'], get_feed, { 'model': moderated_photo_item.get_name(), 'status': ModeratedPhoto.STATUS_UNKNOWN } ),
    url( r'^%s/(?P<permalink>[\w\-_]+)/%s/$' % ( urls['FILM'], urls['POSTER_ADD'], ), add_photo, { 'type': 'film' }, name='add-poster' ),
    url( r'^%s/(?P<permalink>[\w\-_]+)/%s/$' % ( urls['PERSON'], urls['PHOTO_ADD'], ), add_photo, { 'type': 'person' }, name='add-person-photo' ),
    url( r'^film/(?P<permalink>[\w\-_]+)/image/$', image),
)
