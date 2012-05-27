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

import re

import haystack
from haystack.utils import Highlighter

class SolrHighlighter( Highlighter ):
    def __init__( self, query, **kwargs ):
        query = ' '.join( query )
        kwargs['max_length'] = 350

        self.query = ' '.join( re.findall( r'<em>([^<]*)</em>', query ) )
        
        super( SolrHighlighter, self ).__init__( self.query, **kwargs )


def get_dictionaries( site=None ):
    if site is None:
        site = haystack.site

    models = {}
    indexes = {}
    for model, index in site.get_indexes().items():
        model = "%s.%s" % ( model._meta.app_label, model._meta.module_name )
        models[ model ] = index.short_name
        indexes[ index.short_name ] = model
    return models, indexes

def get_model_short_name( name ):
    short_model_names, indexes = get_dictionaries()
    return short_model_names[ name ]

def get_model_from_short_name( name ):
    short_model_names, indexes = get_dictionaries()
    return indexes[ name ]

def get_available_languages():
    # TODO: this should be taken from settings
    #  [ l for l, n in settings.LANGUAGES ]
    return [ 'en', 'pl' ]
