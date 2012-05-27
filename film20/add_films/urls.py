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

from film20.add_films.models import AddedFilm, moderated_added_film
from film20.moderation.views import moderate_item, get_feed

from film20.add_films.views import *

urlpatterns = patterns( '',
    url( r'^%s/manual/$' % ( urls["ADD_FILMS"] ), add_film, name="add-film-manual" ),
    url( r'^%s/manual/(?P<id>\d+)/$' % ( urls["ADD_FILMS"] ), edit_film, name="edit-added-film" ),
    url( r'^%s/manual/add-person/$' % ( urls["ADD_FILMS"] ), add_person, name="add-person-manual" ),
    url( r'^%s/ajax/person_list/$' % ( urls["ADD_FILMS"] ), ajax_person_list, name="person-list-ajax" ),
    url( r'^%s/ajax/country_list/$' % ( urls["ADD_FILMS"] ), ajax_country_list, name="country-list-ajax" ),
    # TODO: put in better place
    url( r'^%s/(?P<permalink>[\w\-_]+)/%s/' % ( urls["FILM"], urls["EDIT_CAST"] ), edit_cast, name="edit-film-cast" ),
)
