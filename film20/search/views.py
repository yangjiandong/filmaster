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

import logging
logger = logging.getLogger(__name__)

from django import http
from django.db.models import Q
from django.http import Http404
from django.conf import settings
from django.utils import simplejson
from django.template import RequestContext
from django.contrib.auth.models import User

from django.shortcuts import render_to_response
from django.views.generic import View, TemplateView
from django.utils.translation import gettext_lazy as _


import haystack.views as haystack_views

from film20.config.urls import *
from film20.tagging.models import Tag
from film20.core.models import Film, Person

from film20.search import search
from film20.search.models import QueuedItem
from film20.search.utils import get_model_short_name
from film20.search.forms import model_choices, SearchForm


class SearchView( haystack_views.SearchView ):    
    def __init__( self, template=templates["SEARCH"], load_all=True, form_class=SearchForm, searchqueryset=None, context_class=RequestContext, limit=None ):
        super( SearchView, self ).__init__( template, load_all, form_class, searchqueryset, context_class )
        self.limit = limit

    def create_response(self):
        """
        Generates the actual HttpResponse to send back to the user.
        """

        facets = []
        try:
            raw_facets = self.results.facet_counts() if self.results else None
            tmp_facets = {}
            if raw_facets is not None:
                for name, length in raw_facets['fields']['django_ct']:
                    if length > 0:
                        results = self.results.narrow( 'django_ct:%s' % name )
                        name = get_model_short_name( name )
                        tmp_facets[name] = {
                            'name': name, 'count': length,
                            'results': results[:self.limit] if self.limit else results
                        }
            
            # sort by default order
            for model, name in model_choices():
                if tmp_facets.has_key( model ):
                    facets.append( tmp_facets[model] )

        except: 
            # on error set empty result
            pass

        context = {
            'query': self.query,
            'model': ''.join( self.form.cleaned_data['t'] ) if self.form.is_valid() else '',
            'form': self.form,
            'full': self.limit is None,
            'facets': facets
        }
        context.update( self.extra_context() )
        
        return render_to_response( self.template, context, context_instance=self.context_class( self.request ) )


class AutocompleteView( View ):

    models = ( Film, Person )

    def get( self, request, *args, **kwargs ):
        return self.render_to_response( self.search() )

    def render_to_response( self, result, **httpresponse_kwargs ):
        content = simplejson.dumps( result )
        if 'callback' in self.request.GET:
            content = "%s(%s)" % ( self.request.GET['callback'], content )

        return http.HttpResponse( content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def search( self ):
        sqs = search( self.get_query(), models=self.models, limit=self.get_limit() )
        return [ self.mapping( x.object, x.model_name ) for x in sqs ]

    def get_query( self ):
        return self.request.GET.get( 'term', '' )

    def get_limit( self ):
        return int( self.request.GET.get( 'limit', '10' ) )

    def mapping( self, obj, type ):
        mapping = {
            'id': obj.pk,
            'category': type,
        }
        fun = getattr( self, 'mapping_%s' % type, None )
        if fun:
            mapping.update( fun( obj ) )
        return mapping

    def mapping_film( self, obj ):
        return {
            'url'        : obj.get_absolute_url(), 
            'value'      : "%s (%s)" % ( obj.get_title(), obj.release_year ), 
            'description': ','.join( [ str( t ) for t in obj.top_directors()[:2] ] ),
            'image'      : obj.get_image( 30 ),
            'category'   : str( _( 'TV Series' ) if obj.is_tv_series else _( 'Film' ) ),
        }

    def mapping_person( self, obj ):
         return {
            'url'        : obj.get_absolute_url(), 
            'value'      : '%s %s' % ( obj.name, obj.surname ), 
            'description': '',
            'image'      : obj.get_image( 30 ),
            'category'   : str( _( 'Person' ) ),
         }


class FilmAutocompleteView( AutocompleteView ):
    models = ( Film, )

    def render_to_response( self, result, **httpresponse_kwargs ):
        return http.HttpResponse( '\n'.join( result ) if len( result ) else '',
                                 content_type='text/plain',
                                 **httpresponse_kwargs)

    def mapping( self, film, type ):
        localized = film.get_localized_title()
        title = film.title.replace( '|', '&verticalline;' )
        disp = ( "%s / %s" % ( film.title, localized ) if localized and localized != film.title else film.title ).replace( '|', '&verticalline;' )
        return "%s [%d]|%s [%d]|film/%s|%d" % ( disp, film.release_year, title, film.release_year, film.permalink, film.pk )

    def get_query( self ):
        return self.request.GET.get( 'q', '' )


class PersonAutocompleteView( FilmAutocompleteView ):
    models = ( Person, )

    def mapping( self, person, type ):
        return "%s %s" % ( person.name, person.surname )


class UserAutocompleteView( FilmAutocompleteView ):
    models = ( User, )

    def mapping( self, user, type ):
        return user.username


class TagAutocompleteView( FilmAutocompleteView ):
    def search( self ):
      tags = Tag.objects.filter( Q( name__istartswith=self.get_query() ), LANG=settings.LANGUAGE_CODE ).order_by( "name" )[:self.get_limit()];
      return map( lambda t: unicode( t ), tags )


from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test

class SolrStats( TemplateView ):
    template_name = "search/stats.html"

    def get_context_data( self, *args, **kwargs ):
        try:
            from film20.search.solr_helper import build_daemon, configuration, is_supported
            is_supported = is_supported()
        except Exception, e:
            is_supported = False

        daemon = build_daemon()
        context = super( SolrStats, self ).get_context_data( *args, **kwargs )
        context.update({
            'solr': daemon,
            'is_supported': is_supported,
            'configuration': configuration,
            'queue': QueuedItem.objects.get_for_language().count()
        })
        return context

    @method_decorator( user_passes_test( lambda u: u.is_superuser ) )
    def dispatch( self, *args, **kwargs ):
        return super( SolrStats, self ).dispatch( *args, **kwargs )

    def render_json_response( self, result, **httpresponse_kwargs ):
        content = simplejson.dumps( result )
        if 'callback' in self.request.GET:
            content = "%s(%s)" % ( self.request.GET['callback'], content )

        return http.HttpResponse( content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)


    def post( self, *args, **kwargs ):
        context = self.get_context_data()
        daemon = context.get( 'solr' )
        if 'stop' in self.request.POST: daemon.stop()
        elif 'start' in self.request.POST: daemon.start()
        elif 'restart' in self.request.POST: daemon.restart()
        elif 'update_queue' in self.request.POST: daemon.update_queue()

        data = {
            'is_active': daemon.is_active(),
            'stats': daemon.get_stats(),
            'queue': QueuedItem.objects.get_for_language().count()
        }

        return self.render_json_response( data )

autocomplete = AutocompleteView.as_view()
film_autocomplete = FilmAutocompleteView.as_view()
person_autocomplete = PersonAutocompleteView.as_view()
user_autocomplete = UserAutocompleteView.as_view()
tag_autocomplete = TagAutocompleteView.as_view()
solr_stats = SolrStats.as_view()

