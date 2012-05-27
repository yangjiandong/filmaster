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
from film20.search.views import *
from film20.config.urls import *

try:
    import haystack
    haystack.autodiscover()
except Exception, e:
    # fix for http://jira.filmaster.org/browse/FLM-597
    print "Exception on autodiscover in urls: ", e
    pass

searchpatterns = patterns('',

    url( r'^%s/$' % urls[ "SEARCH" ], SearchView( limit=4 ), name='search' ),
    url( r'^%s-full/$' % urls[ "SEARCH" ], SearchView(), name='search-full' ),
    url( r'^search/autocomplete/$', autocomplete, name='search-autocomplete' ),

    url(r'^ajax/%s/$' % urls["SEARCH"], user_autocomplete, name='search_user_autocomplete'),
    url(r'^ajax/%s/$' % urls["SEARCH_FILM"], film_autocomplete, name='search_film_autocomplete'),
    url(r'^ajax/%s/$' % urls["SEARCH_PERSON"], person_autocomplete, name='search_person_autocomplete'),

    url(r'^ajax/search_tag_autocomplete/$', tag_autocomplete, name='search_tag_autocomplete'),
    
    url( r'^%s/solr/stats/$' % urls[ "SEARCH" ], solr_stats, name='solr-stats' ),

)
