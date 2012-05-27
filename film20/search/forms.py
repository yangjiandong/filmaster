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

from django import forms
from django.db import models
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

import haystack
from haystack.backends import SQ
from haystack.forms import SearchForm as _SearchForm

from film20.search.utils import get_model_short_name, get_model_from_short_name

def model_choices(site=None):
    if site is None:
        site = haystack.site
    
    models = sorted( [ ( m, k.order ) for m, k in site.get_indexes().items() ], key=lambda x: x[1] )
    return [ ("%s" % get_model_short_name( "%s.%s" % ( m[0]._meta.app_label, m[0]._meta.module_name ) ), 
              capfirst( unicode( m[0]._meta.verbose_name_plural ) ) ) for m in models ]

class SearchForm( _SearchForm ):
    QUERY_PARAM_NAME='q'
    MODELS_PARAM_NAME='t'

    def __init__( self, *args, **kwargs ):
        super( SearchForm, self ).__init__( *args, **kwargs )
        self.fields[ self.MODELS_PARAM_NAME ] = forms.MultipleChoiceField( choices=model_choices(), 
                                                          required=False, label=_('Search In'), widget=forms.CheckboxSelectMultiple )

    def get_models(self):
        """
        Return list of model classes in the index.
        """
        search_models = []
        
        if self.is_valid():
            for model in self.cleaned_data[ self.MODELS_PARAM_NAME ]:
                model = get_model_from_short_name( model )
                search_models.append( models.get_model( *model.split( '.' ) ) )
        
        return search_models

    
    def search( self ):
        if not self.is_valid():
            return self.no_query_found()
        
        if not self.cleaned_data[ self.QUERY_PARAM_NAME ]:
            return self.no_query_found()

        self.clean()

        q = self.cleaned_data[ self.QUERY_PARAM_NAME ].lower();
        models = self.get_models()
        
        # add models
        sqs = self.searchqueryset.models( *models )
        
        # ignore letters
        keywords  = [ sqs.query.clean( k ) for k in q.split() if len( k ) > 1 ]

        # search word by word
        for keyword in keywords:
            sqs.query.add_filter( 
                SQ( 
                    SQ( exact = "%s^2.0" % keyword ) | \
                    SQ( title = "%s^1.0" % keyword ) | \
                    SQ( content = "%s^0.5" % keyword )
                )
            )

        # add exact match
        sqs.query.add_filter( SQ( exact="%s^3.0" % sqs.query.clean( q ) ), True )

        # order by score and popularity
        sqs = sqs.order_by( '-score', '-popularity' )
        
        # add highlight
        sqs = sqs.highlight()
        
        # add faceting by django_ct
        sqs = sqs.facet( 'django_ct' )

        if self.load_all:
            sqs = sqs.load_all()

        return sqs
