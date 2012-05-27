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

from haystack.backends import SQ
from haystack.query import SearchQuerySet


def search( query, limit=20, models=None, as_list=False ):
    print "Searching for: %s" % query
    if not query:
        return []

    try:
        sqs = SearchQuerySet()

        # clean query
        q = sqs.query.clean( query )

        # add models
        if models is not None:
            if not isinstance( models, ( list, tuple ) ):
                models = ( models, )
            sqs = sqs.models( *models )

        # ignore letters
        keywords  = [ k for k in q.split() if len( k ) > 1 ]

        # search word by word
        for keyword in keywords:
            sqs.query.add_filter( SQ( title="%s^2.0" % keyword ) )

        # order by score and popularity
        sqs = sqs.order_by( '-score', '-popularity' )
        
        # add highlight
        sqs = sqs.highlight()
        sqs = sqs[:limit]

    except Exception, e: # on error show empty result 
        print e # TODO: log error
        sqs = []

    return [ x.object for x in filter( lambda x: x is not None, sqs ) ] if as_list else sqs


def search_user( query, limit=20, as_list=True ):
    from django.contrib.auth.models import User
    return search( query, models=User, limit=limit, as_list=as_list )

def search_film( query, limit=20, as_list=True ):
    from film20.core.models import Film
    return search( query, models=Film, limit=limit, as_list=as_list )

def search_person( query, limit=20, as_list=True ):
    from film20.core.models import Person
    return search( query, models=Person, limit=limit, as_list=as_list )

